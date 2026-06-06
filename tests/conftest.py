import asyncio
import os
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ.setdefault("DATA_DIR", "/tmp/wol_test_data")
os.environ["ADMIN_PASSWORD"] = "admin"
os.environ["FERNET_KEY"] = "O_I47tB3QrIKML4o8CyjD247j8h1NVKpPnmcrGNmjLI="

import backend.app.database as db_module
from backend.app.database import get_db

TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    TEST_ENGINE, class_=AsyncSession, expire_on_commit=False
)

db_module.engine = TEST_ENGINE
db_module.async_session = TestSessionLocal

from backend.app.main import app

from tests.virtual_device.device_simulator import DeviceState, VirtualDevicePool
from tests.virtual_device.ping_simulator import PingSimulator
from tests.virtual_device.shutdown_interceptor import ShutdownInterceptor
from tests.virtual_device.wol_interceptor import WolInterceptor


def _get_or_create_event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        pass
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


async def _noop_ping_loop():
    await asyncio.Event().wait()


async def _clear_test_data():
    from sqlalchemy import delete
    from backend.app.models import (
        Device,
        DeviceGroup,
        NotificationChannel,
        OperationLog,
        ScheduledTask,
        Setting,
        TriggerSource,
    )

    try:
        async with TestSessionLocal() as session:
            await session.execute(delete(OperationLog))
            await session.execute(delete(ScheduledTask))
            await session.execute(delete(Device))
            await session.execute(delete(TriggerSource))
            await session.execute(delete(NotificationChannel))
            await session.execute(delete(DeviceGroup))
            await session.execute(delete(Setting))
            await session.commit()
    except Exception:
        pass


@pytest.fixture
def virtual_pool():
    pool = VirtualDevicePool()
    pool.register("AA:BB:CC:DD:EE:01", "192.168.1.100", "linux", DeviceState.OFFLINE)
    pool.register("AA:BB:CC:DD:EE:02", "192.168.1.101", "windows", DeviceState.ONLINE)
    pool.register("AA:BB:CC:DD:EE:03", "192.168.1.102", "macos", DeviceState.ONLINE)
    return pool


@pytest.fixture
def client(virtual_pool):
    loop = _get_or_create_event_loop()
    loop.run_until_complete(_clear_test_data())

    wol_interceptor = WolInterceptor(virtual_pool)
    shutdown_interceptor = ShutdownInterceptor(virtual_pool)
    ping_sim = PingSimulator(virtual_pool)

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    patches = [
        patch("backend.app.services.wol.send_wol", wol_interceptor.send_wol),
        patch("backend.app.services.shutdown.send_shutdown", shutdown_interceptor.send_shutdown),
        patch("backend.app.services.ping_monitor._ping", ping_sim.ping_host),
        patch("backend.app.services.ping_monitor.ping_loop", _noop_ping_loop),
        patch("backend.app.services.bemfa.start_bemfa_clients", new_callable=AsyncMock),
        patch("backend.app.services.mqtt.start_mqtt_clients", new_callable=AsyncMock),
        patch("backend.app.services.telegram_bot.start_telegram_bots", new_callable=AsyncMock),
        patch("backend.app.services.notification.notify_all", new_callable=AsyncMock),
    ]

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()
    virtual_pool.reset_all()


@pytest.fixture
def auth_headers(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seeded_devices(client, auth_headers):
    devices = [
        {
            "name": "Linux Server",
            "ip": "192.168.1.100",
            "mac": "AA:BB:CC:DD:EE:01",
            "device_type": "linux",
            "shutdown_enabled": True,
            "shutdown_user": "root",
            "shutdown_password": "test123",
            "shutdown_auth_type": "password",
        },
        {
            "name": "Windows PC",
            "ip": "192.168.1.101",
            "mac": "AA:BB:CC:DD:EE:02",
            "device_type": "windows",
            "shutdown_enabled": True,
            "shutdown_user": "admin",
            "shutdown_password": "test123",
            "shutdown_auth_type": "password",
        },
        {
            "name": "MacBook",
            "ip": "192.168.1.102",
            "mac": "AA:BB:CC:DD:EE:03",
            "device_type": "macos",
            "shutdown_enabled": True,
            "shutdown_user": "user",
            "shutdown_password": "test123",
            "shutdown_auth_type": "password",
        },
    ]
    created = []
    for dev_data in devices:
        resp = client.post("/api/devices", json=dev_data, headers=auth_headers)
        assert resp.status_code == 201, f"Failed to create device: {resp.text}"
        created.append(resp.json())
    return created

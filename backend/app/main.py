import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select

from .config import settings
from .database import init_db, async_session
from .models.user import User
from .auth import hash_password

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("xiaoxue_wol")

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _ensure_admin()

    from .services.ping_monitor import ping_loop
    from .services.scheduler import scheduler_service
    from .services.bemfa import start_bemfa_clients
    from .services.mqtt import start_mqtt_clients

    ping_task = asyncio.create_task(ping_loop())
    await scheduler_service.start()
    await start_bemfa_clients()
    await start_mqtt_clients()

    yield

    ping_task.cancel()
    scheduler_service.stop()
    from .services.bemfa import stop_all as stop_bemfa
    from .services.mqtt import stop_all as stop_mqtt
    stop_bemfa()
    stop_mqtt()


app = FastAPI(title="XiaoXue_WoL", version="1.0.0", lifespan=lifespan)

# --- Register routers ---
from .routers import auth, devices, groups, schedules, channels, triggers, logs, dashboard, scan  # noqa: E402

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(groups.router)
app.include_router(schedules.router)
app.include_router(channels.router)
app.include_router(triggers.router)
app.include_router(triggers.mgmt_router)
app.include_router(logs.router)
app.include_router(dashboard.router)
app.include_router(scan.router)


# --- WebSocket for live device status ---
@app.websocket("/ws/status")
async def ws_status(ws: WebSocket):
    await ws.accept()
    from .services.ping_monitor import register_ws, unregister_ws
    register_ws(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        unregister_ws(ws)


# --- Serve frontend SPA ---
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = FRONTEND_DIR / full_path
        if file.exists() and file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIR / "index.html")


async def _ensure_admin():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        if not result.scalar_one_or_none():
            admin = User(username=settings.ADMIN_USERNAME, password_hash=hash_password(settings.ADMIN_PASSWORD))
            db.add(admin)
            await db.commit()
            logger.info("Default admin user created (username=%s)", settings.ADMIN_USERNAME)

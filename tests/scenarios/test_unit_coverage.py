"""
Unit tests for core utility modules: crypto, auth, proxy, config.
These improve coverage on non-router code paths.
"""
import pytest
from unittest.mock import patch, AsyncMock


class TestCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        from backend.app.crypto import encrypt, decrypt
        original = "my-secret-password-123"
        encrypted = encrypt(original)
        assert encrypted != original
        assert decrypt(encrypted) == original

    def test_encrypt_empty_returns_empty(self):
        from backend.app.crypto import encrypt
        assert encrypt("") == ""

    def test_decrypt_empty_returns_empty(self):
        from backend.app.crypto import decrypt
        assert decrypt("") == ""

    def test_encrypt_special_chars(self):
        from backend.app.crypto import encrypt, decrypt
        special = "P@$$w0rd!#%^&*()"
        encrypted = encrypt(special)
        assert decrypt(encrypted) == special


class TestAuth:
    def test_hash_and_verify_password(self):
        from backend.app.auth import hash_password, verify_password
        hashed = hash_password("test123")
        assert verify_password("test123", hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_create_access_token(self):
        from backend.app.auth import create_access_token
        from jose import jwt
        from backend.app.config import settings
        token = create_access_token(data={"sub": "testuser"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        from datetime import timedelta
        from backend.app.auth import create_access_token
        from jose import jwt
        from backend.app.config import settings
        token = create_access_token(data={"sub": "u"}, expires_delta=timedelta(minutes=5))
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "u"


class TestProxy:
    def test_build_proxy_url_disabled(self):
        from backend.app.services.proxy import build_proxy_url
        assert build_proxy_url({"proxy_enabled": False}) is None

    def test_build_proxy_url_no_host(self):
        from backend.app.services.proxy import build_proxy_url
        assert build_proxy_url({"proxy_enabled": True, "proxy_host": ""}) is None

    def test_build_proxy_url_http(self):
        from backend.app.services.proxy import build_proxy_url
        url = build_proxy_url({
            "proxy_enabled": True,
            "proxy_type": "http",
            "proxy_host": "127.0.0.1",
            "proxy_port": 7890,
            "proxy_username": "",
            "proxy_password": "",
        })
        assert url == "http://127.0.0.1:7890"

    def test_build_proxy_url_socks5(self):
        from backend.app.services.proxy import build_proxy_url
        url = build_proxy_url({
            "proxy_enabled": True,
            "proxy_type": "socks5",
            "proxy_host": "192.168.1.1",
            "proxy_port": 1080,
            "proxy_username": "",
            "proxy_password": "",
        })
        assert url == "socks5://192.168.1.1:1080"

    def test_build_proxy_url_with_auth(self):
        from backend.app.services.proxy import build_proxy_url
        url = build_proxy_url({
            "proxy_enabled": True,
            "proxy_type": "http",
            "proxy_host": "proxy.example.com",
            "proxy_port": 8080,
            "proxy_username": "user",
            "proxy_password": "pass",
        })
        assert url == "http://user:pass@proxy.example.com:8080"


class TestConfig:
    def test_app_version_exists(self):
        from backend.app.config import APP_VERSION
        assert APP_VERSION is not None
        assert len(APP_VERSION) > 0

    def test_settings_attributes(self):
        from backend.app.config import settings
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(settings, "TZ")
        assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


class TestTimezone:
    def test_tz_now_returns_datetime(self):
        from backend.app.tz import tz_now
        from datetime import datetime
        now = tz_now()
        assert isinstance(now, datetime)
        assert now.tzinfo is not None


class TestDeviceSimulator:
    def test_virtual_device_wol(self):
        from tests.virtual_device.device_simulator import VirtualDevice, DeviceState
        dev = VirtualDevice("AA:BB:CC:DD:EE:01", "10.0.0.1", "linux", DeviceState.OFFLINE)
        ok, msg = dev.receive_wol()
        assert ok is True
        assert dev.state == DeviceState.ONLINE
        assert len(dev.action_log) == 1

    def test_virtual_device_shutdown_online(self):
        from tests.virtual_device.device_simulator import VirtualDevice, DeviceState
        dev = VirtualDevice("AA:BB:CC:DD:EE:01", "10.0.0.1", "linux", DeviceState.ONLINE)
        ok, msg = dev.receive_shutdown("linux")
        assert ok is True
        assert dev.state == DeviceState.OFFLINE

    def test_virtual_device_shutdown_offline_fails(self):
        from tests.virtual_device.device_simulator import VirtualDevice, DeviceState
        dev = VirtualDevice("AA:BB:CC:DD:EE:01", "10.0.0.1", "linux", DeviceState.OFFLINE)
        ok, msg = dev.receive_shutdown("linux")
        assert ok is False
        assert dev.state == DeviceState.OFFLINE

    def test_virtual_device_ping(self):
        from tests.virtual_device.device_simulator import VirtualDevice, DeviceState
        dev_online = VirtualDevice("AA:BB:CC:DD:EE:01", "10.0.0.1", "linux", DeviceState.ONLINE)
        dev_offline = VirtualDevice("AA:BB:CC:DD:EE:02", "10.0.0.2", "linux", DeviceState.OFFLINE)
        assert dev_online.get_ping_result() is True
        assert dev_offline.get_ping_result() is False

    def test_virtual_device_reset(self):
        from tests.virtual_device.device_simulator import VirtualDevice, DeviceState
        dev = VirtualDevice("AA:BB:CC:DD:EE:01", "10.0.0.1", "linux", DeviceState.OFFLINE)
        dev.receive_wol()
        assert dev.state == DeviceState.ONLINE
        dev.reset()
        assert dev.state == DeviceState.OFFLINE
        assert dev.action_log == []

    def test_virtual_pool_register_and_get(self):
        from tests.virtual_device.device_simulator import VirtualDevicePool, DeviceState
        pool = VirtualDevicePool()
        pool.register("11:22:33:44:55:66", "10.0.0.1", "linux", DeviceState.OFFLINE)
        dev = pool.get_by_mac("11:22:33:44:55:66")
        assert dev is not None
        assert dev.ip == "10.0.0.1"
        dev_by_ip = pool.get_by_ip("10.0.0.1")
        assert dev_by_ip is not None
        assert dev_by_ip.mac == "11:22:33:44:55:66"

    def test_virtual_pool_reset_all(self):
        from tests.virtual_device.device_simulator import VirtualDevicePool, DeviceState
        pool = VirtualDevicePool()
        pool.register("11:22:33:44:55:66", "10.0.0.1", "linux", DeviceState.OFFLINE)
        pool.get_by_mac("11:22:33:44:55:66").receive_wol()
        pool.reset_all()
        assert pool.get_by_mac("11:22:33:44:55:66").state == DeviceState.OFFLINE

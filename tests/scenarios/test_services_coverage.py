"""
Service-layer unit tests to push coverage above 90%.
Tests the actual service functions with mocked I/O (no network, no real SSH).
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock


# ============ WOL SERVICE ============

class TestWolService:
    @pytest.mark.asyncio
    async def test_send_wol_success(self):
        with patch("backend.app.services.wol.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=None)
            from backend.app.services.wol import send_wol
            ok, msg = await send_wol("AA:BB:CC:DD:EE:FF")
            assert ok is True
            assert "已发送魔术包" in msg

    @pytest.mark.asyncio
    async def test_send_wol_invalid_mac(self):
        from backend.app.services.wol import send_wol
        ok, msg = await send_wol("INVALID")
        assert ok is False
        assert "格式无效" in msg

    @pytest.mark.asyncio
    async def test_send_wol_with_dashes(self):
        with patch("backend.app.services.wol.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=None)
            from backend.app.services.wol import send_wol
            ok, msg = await send_wol("AA-BB-CC-DD-EE-FF")
            assert ok is True

    @pytest.mark.asyncio
    async def test_send_wol_exception(self):
        with patch("backend.app.services.wol.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(side_effect=OSError("Network error"))
            from backend.app.services.wol import send_wol
            ok, msg = await send_wol("AA:BB:CC:DD:EE:FF")
            assert ok is False
            assert "失败" in msg


# ============ SHUTDOWN SERVICE ============

class TestShutdownService:
    @pytest.mark.asyncio
    async def test_shutdown_with_password_success(self):
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 0

        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            with patch("backend.app.services.shutdown.shutil.which", return_value="/usr/bin/sshpass"):
                from backend.app.services.shutdown import send_shutdown
                ok, msg = await send_shutdown("10.0.0.1", "root", "pass123", device_type="linux")
                assert ok is True
                assert "已发送" in msg

    @pytest.mark.asyncio
    async def test_shutdown_with_password_no_sshpass(self):
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 0

        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            with patch("backend.app.services.shutdown.shutil.which", return_value=None):
                from backend.app.services.shutdown import send_shutdown
                ok, msg = await send_shutdown("10.0.0.1", "root", "pass123", device_type="windows")
                assert ok is True

    @pytest.mark.asyncio
    async def test_shutdown_with_key(self):
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 0

        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            from backend.app.services.shutdown import send_shutdown
            key = "-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n-----END OPENSSH PRIVATE KEY-----"
            ok, msg = await send_shutdown("10.0.0.1", "root", private_key=key, device_type="macos")
            assert ok is True

    @pytest.mark.asyncio
    async def test_shutdown_with_key_no_pem_header(self):
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 0

        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            from backend.app.services.shutdown import send_shutdown
            ok, msg = await send_shutdown("10.0.0.1", "root", private_key="rawkeydata", device_type="linux")
            assert ok is True

    @pytest.mark.asyncio
    async def test_shutdown_no_password_no_key(self):
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 0

        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            from backend.app.services.shutdown import send_shutdown
            ok, msg = await send_shutdown("10.0.0.1", "user", device_type="linux")
            assert ok is True

    @pytest.mark.asyncio
    async def test_shutdown_failure_nonzero_exit(self):
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Permission denied"))
        mock_proc.returncode = 255

        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            from backend.app.services.shutdown import send_shutdown
            ok, msg = await send_shutdown("10.0.0.1", "root", "pass", device_type="linux")
            assert ok is False
            assert "关机失败" in msg

    @pytest.mark.asyncio
    async def test_shutdown_timeout(self):
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_proc.returncode = None

        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            with patch("backend.app.services.shutdown.asyncio.wait_for",
                       side_effect=asyncio.TimeoutError()):
                from backend.app.services.shutdown import send_shutdown
                ok, msg = await send_shutdown("10.0.0.1", "root", "pass", device_type="linux")
                assert ok is False
                assert "超时" in msg

    @pytest.mark.asyncio
    async def test_shutdown_exception(self):
        with patch("backend.app.services.shutdown.asyncio.create_subprocess_exec",
                   side_effect=OSError("SSH not found")):
            from backend.app.services.shutdown import send_shutdown
            ok, msg = await send_shutdown("10.0.0.1", "root", "pass", device_type="linux")
            assert ok is False
            assert "异常" in msg


# ============ NOTIFICATION SERVICE ============

class TestNotificationService:
    @pytest.mark.asyncio
    async def test_send_notification_unknown_type(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "unknown_type"
        ch.name = "test"
        result = await send_notification(ch, "Test", "Body")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_email(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "email"
        ch.name = "email_ch"
        ch.config = {
            "host": "smtp.example.com",
            "port": 587,
            "username": "user@example.com",
            "from_addr": "user@example.com",
            "to_addr": "to@example.com",
            "password": "pass",
            "tls": True,
        }
        with patch("backend.app.services.notification.aiosmtplib.send", new_callable=AsyncMock):
            result = await send_notification(ch, "Subject", "Body")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_notification_webhook(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "webhook"
        ch.name = "webhook_ch"
        ch.config = {
            "url": "https://hook.example.com/notify",
            "method": "POST",
            "headers": {},
            "body_template": {"title": "{title}", "body": "{body}"},
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        async def fake_get_client(**kwargs):
            return mock_client

        with patch("backend.app.services.proxy.get_httpx_client", side_effect=fake_get_client):
            result = await send_notification(ch, "Hello", "World")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_notification_webhook_get_method(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "webhook"
        ch.name = "webhook_get"
        ch.config = {
            "url": "https://hook.example.com/ping",
            "method": "GET",
            "headers": '{"X-Custom": "val"}',
            "body_template": '{"action": "{title}"}',
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        async def fake_get_client(**kwargs):
            return mock_client

        with patch("backend.app.services.proxy.get_httpx_client", side_effect=fake_get_client):
            result = await send_notification(ch, "Title", "Body")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_notification_telegram(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "telegram"
        ch.name = "tg_ch"
        ch.config = {"bot_token": "123:ABC", "chat_ids": "111,222"}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=MagicMock())
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        async def fake_get_client(**kwargs):
            return mock_client

        with patch("backend.app.services.proxy.get_httpx_client", side_effect=fake_get_client):
            result = await send_notification(ch, "Title", "Body")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_telegram_empty_token(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "telegram"
        ch.name = "tg_empty"
        ch.config = {"bot_token": "", "chat_ids": ""}
        result = await send_notification(ch, "Title", "Body")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_exception(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "email"
        ch.name = "broken"
        ch.config = {"host": "smtp.test.com", "to_addr": "x@y.com"}
        with patch("backend.app.services.notification.aiosmtplib.send",
                   new_callable=AsyncMock, side_effect=Exception("SMTP error")):
            result = await send_notification(ch, "T", "B")
            assert result is False

    @pytest.mark.asyncio
    async def test_notify_all(self):
        from backend.app.services.notification import notify_all
        mock_ch = MagicMock()
        mock_ch.type = "bark"
        mock_ch.name = "test"
        mock_ch.config = {}

        with patch("backend.app.services.notification.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_ch]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.notification.send_notification", new_callable=AsyncMock, return_value=True):
                await notify_all("Title", "Body", event="trigger")

    @pytest.mark.asyncio
    async def test_notify_all_success_event(self):
        from backend.app.services.notification import notify_all
        with patch("backend.app.services.notification.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await notify_all("Title", "Body", event="success")

    @pytest.mark.asyncio
    async def test_notify_all_exception_handling(self):
        from backend.app.services.notification import notify_all
        mock_ch = MagicMock()
        mock_ch.name = "broken"

        with patch("backend.app.services.notification.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_ch]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.notification.send_notification",
                       new_callable=AsyncMock, side_effect=Exception("fail")):
                await notify_all("T", "B")

    @pytest.mark.asyncio
    async def test_send_webhook_string_headers_and_template(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "webhook"
        ch.name = "str_tpl"
        ch.config = {
            "url": "https://hook.example.com/test",
            "method": "POST",
            "headers": "invalid-json",
            "body_template": "not-json-either",
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        async def fake_get_client(**kwargs):
            return mock_client

        with patch("backend.app.services.proxy.get_httpx_client", side_effect=fake_get_client):
            result = await send_notification(ch, "T", "B")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_telegram_list_chat_ids(self):
        from backend.app.services.notification import send_notification
        ch = MagicMock()
        ch.type = "telegram"
        ch.name = "tg_list"
        ch.config = {"bot_token": "123:ABC", "chat_ids": [111, 222]}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=MagicMock())
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        async def fake_get_client(**kwargs):
            return mock_client

        with patch("backend.app.services.proxy.get_httpx_client", side_effect=fake_get_client):
            result = await send_notification(ch, "T", "B")
            assert result is True


# ============ PING MONITOR ============

class TestPingMonitor:
    def test_register_unregister_ws(self):
        from backend.app.services.ping_monitor import (
            register_ws, unregister_ws, has_active_clients, _ws_clients
        )
        _ws_clients.clear()
        mock_ws = MagicMock()
        register_ws(mock_ws)
        assert has_active_clients() is True
        unregister_ws(mock_ws)
        assert has_active_clients() is False

    def test_register_pending_check(self):
        from backend.app.services.ping_monitor import register_pending_check, _pending_checks
        register_pending_check(1, "wake", "Test Device")
        assert 1 in _pending_checks
        assert _pending_checks[1]["action"] == "wake"
        _pending_checks.clear()

    @pytest.mark.asyncio
    async def test_broadcast_status(self):
        from backend.app.services.ping_monitor import _broadcast_status, _ws_clients
        _ws_clients.clear()
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        _ws_clients.add(mock_ws)
        await _broadcast_status(1, True)
        mock_ws.send_text.assert_called_once()
        _ws_clients.clear()

    @pytest.mark.asyncio
    async def test_broadcast_status_dead_ws(self):
        from backend.app.services.ping_monitor import _broadcast_status, _ws_clients
        _ws_clients.clear()
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock(side_effect=Exception("closed"))
        _ws_clients.add(mock_ws)
        await _broadcast_status(1, False)
        assert mock_ws not in _ws_clients
        _ws_clients.clear()


# ============ BEMFA SERVICE ============

class TestBemfaService:
    def test_get_status(self):
        from backend.app.services.bemfa import get_status, _status
        _status.clear()
        _status[1] = "connected"
        assert get_status() == {1: "connected"}
        _status.clear()

    @pytest.mark.asyncio
    async def test_handle_message_wake(self):
        from backend.app.services.bemfa import _handle_message
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.name = "Test"
        mock_device.shutdown_enabled = True

        with patch("backend.app.services.bemfa.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_device
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock, return_value=(True, "OK")):
                with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                    with patch("backend.app.services.ping_monitor.register_pending_check"):
                        with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                            await _handle_message("topic=wol&msg=on", "wol", "AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_handle_message_shutdown(self):
        from backend.app.services.bemfa import _handle_message
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.ip = "10.0.0.1"
        mock_device.name = "Test"
        mock_device.shutdown_enabled = True
        mock_device.shutdown_user = "root"
        mock_device.shutdown_password_enc = "enc"
        mock_device.shutdown_auth_type = "password"
        mock_device.shutdown_key_enc = ""
        mock_device.device_type = "linux"

        with patch("backend.app.services.bemfa.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_device
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.shutdown.send_shutdown", new_callable=AsyncMock, return_value=(True, "OK")):
                with patch("backend.app.crypto.decrypt", return_value="pass"):
                    with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                        with patch("backend.app.services.ping_monitor.register_pending_check"):
                            with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                                await _handle_message("topic=wol&msg=off", "wol", "AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_handle_message_unknown_msg(self):
        from backend.app.services.bemfa import _handle_message
        await _handle_message("topic=wol&msg=unknown", "wol", "AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_handle_message_device_not_found(self):
        from backend.app.services.bemfa import _handle_message
        with patch("backend.app.services.bemfa.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await _handle_message("topic=wol&msg=on", "wol", "FF:FF:FF:FF:FF:FF")

    def test_stop_all(self):
        from backend.app.services.bemfa import stop_all, _tasks, _status
        mock_task = MagicMock()
        _tasks[99] = mock_task
        _status[99] = "connected"
        stop_all()
        mock_task.cancel.assert_called_once()
        assert len(_tasks) == 0
        assert len(_status) == 0

    @pytest.mark.asyncio
    async def test_start_bemfa_clients(self):
        from backend.app.services.bemfa import start_bemfa_clients, _tasks
        mock_trigger = MagicMock()
        mock_trigger.id = 10
        mock_trigger.config = {"uid": "x", "topic": "t", "device_mac": "AA:BB:CC:DD:EE:01"}
        with patch("backend.app.services.bemfa.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_trigger]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await start_bemfa_clients()
        assert 10 in _tasks
        _tasks[10].cancel()
        _tasks.clear()

    @pytest.mark.asyncio
    async def test_handle_message_shutdown_disabled(self):
        from backend.app.services.bemfa import _handle_message
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.name = "Test"
        mock_device.shutdown_enabled = False

        with patch("backend.app.services.bemfa.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_device
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await _handle_message("topic=wol&msg=off", "wol", "AA:BB:CC:DD:EE:01")


# ============ MQTT SERVICE ============

class TestMqttService:
    def test_get_status(self):
        from backend.app.services.mqtt import get_status, _status
        _status.clear()
        _status[2] = "connected"
        assert get_status() == {2: "connected"}
        _status.clear()

    @pytest.mark.asyncio
    async def test_handle_mqtt_wake(self):
        from backend.app.services.mqtt import _handle_mqtt
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.name = "Test"

        with patch("backend.app.services.mqtt.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_device
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock, return_value=(True, "OK")):
                with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                    with patch("backend.app.services.ping_monitor.register_pending_check"):
                        with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                            await _handle_mqtt("wake", "AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_handle_mqtt_shutdown(self):
        from backend.app.services.mqtt import _handle_mqtt
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.ip = "10.0.0.1"
        mock_device.name = "Test"
        mock_device.shutdown_enabled = True
        mock_device.shutdown_user = "root"
        mock_device.shutdown_password_enc = "enc"
        mock_device.shutdown_auth_type = "password"
        mock_device.shutdown_key_enc = ""
        mock_device.device_type = "linux"

        with patch("backend.app.services.mqtt.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_device
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.shutdown.send_shutdown", new_callable=AsyncMock, return_value=(True, "OK")):
                with patch("backend.app.crypto.decrypt", return_value="pass"):
                    with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                        with patch("backend.app.services.ping_monitor.register_pending_check"):
                            with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                                await _handle_mqtt("shutdown", "AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_handle_mqtt_device_not_found(self):
        from backend.app.services.mqtt import _handle_mqtt
        with patch("backend.app.services.mqtt.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await _handle_mqtt("wake", "FF:FF:FF:FF:FF:FF")

    def test_stop_all(self):
        from backend.app.services.mqtt import stop_all, _tasks, _status
        mock_task = MagicMock()
        _tasks[99] = mock_task
        _status[99] = "connected"
        stop_all()
        mock_task.cancel.assert_called_once()
        assert len(_tasks) == 0
        assert len(_status) == 0

    @pytest.mark.asyncio
    async def test_start_mqtt_clients(self):
        from backend.app.services.mqtt import start_mqtt_clients, _tasks
        mock_trigger = MagicMock()
        mock_trigger.id = 20
        mock_trigger.config = {"broker": "localhost", "port": 1883, "topic": "test/#", "device_mac": "AA:BB:CC:DD:EE:01"}
        with patch("backend.app.services.mqtt.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_trigger]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await start_mqtt_clients()
        assert 20 in _tasks
        _tasks[20].cancel()
        _tasks.clear()

    @pytest.mark.asyncio
    async def test_handle_mqtt_shutdown_disabled(self):
        from backend.app.services.mqtt import _handle_mqtt
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.name = "Test"
        mock_device.shutdown_enabled = False

        with patch("backend.app.services.mqtt.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_device
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await _handle_mqtt("shutdown", "AA:BB:CC:DD:EE:01")


# ============ TELEGRAM BOT ============

class TestTelegramBot:
    def test_get_status(self):
        from backend.app.services.telegram_bot import get_status, _status
        _status.clear()
        _status[3] = "connected"
        assert get_status() == {3: "connected"}
        _status.clear()

    def test_stop_all(self):
        from backend.app.services.telegram_bot import stop_all, _bots, _status
        mock_task = MagicMock()
        _bots[99] = mock_task
        _status[99] = "connected"
        stop_all()
        mock_task.cancel.assert_called_once()
        assert len(_bots) == 0
        assert len(_status) == 0

    def test_bot_is_allowed_open(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        assert bot._is_allowed(12345) is True

    def test_bot_is_allowed_restricted(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [111, 222])
        assert bot._is_allowed(111) is True
        assert bot._is_allowed(999) is False

    @pytest.mark.asyncio
    async def test_bot_handle_update_message_command(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        update = {"message": {"text": "/start", "chat": {"id": 100}}}
        await bot.handle_update(update)
        bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_bot_handle_update_unknown_command(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        update = {"message": {"text": "/foobar", "chat": {"id": 100}}}
        await bot.handle_update(update)
        bot.send_message.assert_called()
        call_args = bot.send_message.call_args[0]
        assert "未知命令" in call_args[1]

    @pytest.mark.asyncio
    async def test_bot_handle_callback_devices(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.answer_callback = AsyncMock()
        bot._cmd_devices = AsyncMock()
        update = {
            "callback_query": {
                "id": "cb1",
                "message": {"chat": {"id": 100}},
                "data": "devices",
            }
        }
        await bot.handle_update(update)
        bot._cmd_devices.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_bot_handle_callback_wake(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.answer_callback = AsyncMock()
        bot._action_wake = AsyncMock()
        update = {
            "callback_query": {
                "id": "cb2",
                "message": {"chat": {"id": 100}},
                "data": "wake:5",
            }
        }
        await bot.handle_update(update)
        bot._action_wake.assert_called_once_with(100, 5)

    @pytest.mark.asyncio
    async def test_bot_handle_callback_shutdown(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.answer_callback = AsyncMock()
        bot._action_shutdown = AsyncMock()
        update = {
            "callback_query": {
                "id": "cb3",
                "message": {"chat": {"id": 100}},
                "data": "shutdown:3",
            }
        }
        await bot.handle_update(update)
        bot._action_shutdown.assert_called_once_with(100, 3)

    @pytest.mark.asyncio
    async def test_bot_cmd_devices_empty(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._cmd_devices(100)
        bot.send_message.assert_called()
        assert "暂无设备" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_cmd_devices_with_devices(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        mock_dev = MagicMock()
        mock_dev.id = 1
        mock_dev.name = "Server"
        mock_dev.ip = "10.0.0.1"
        mock_dev.mac = "AA:BB:CC:DD:EE:01"
        mock_dev.is_online = True
        mock_dev.shutdown_enabled = True

        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_dev]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._cmd_devices(100)
        bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_bot_cmd_logs_empty(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._cmd_logs(100)
        assert "暂无" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_cmd_groups_empty(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._cmd_groups(100)
        assert "暂无分组" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_action_wake(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        mock_dev = MagicMock()
        mock_dev.id = 1
        mock_dev.mac = "AA:BB:CC:DD:EE:01"
        mock_dev.name = "Server"

        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_dev
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock, return_value=(True, "Sent")):
                with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                    with patch("backend.app.services.ping_monitor.register_pending_check"):
                        with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                            await bot._action_wake(100, 1)

        bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_bot_action_shutdown(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        mock_dev = MagicMock()
        mock_dev.id = 1
        mock_dev.ip = "10.0.0.1"
        mock_dev.mac = "AA:BB:CC:DD:EE:01"
        mock_dev.name = "Server"
        mock_dev.shutdown_enabled = True
        mock_dev.shutdown_user = "root"
        mock_dev.shutdown_password_enc = "enc"
        mock_dev.shutdown_auth_type = "password"
        mock_dev.shutdown_key_enc = ""
        mock_dev.device_type = "linux"

        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_dev
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.shutdown.send_shutdown", new_callable=AsyncMock, return_value=(True, "OK")):
                with patch("backend.app.crypto.decrypt", return_value="pass"):
                    with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                        with patch("backend.app.services.ping_monitor.register_pending_check"):
                            with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                                await bot._action_shutdown(100, 1)

        bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_bot_action_wake_device_not_found(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._action_wake(100, 999)
        assert "不存在" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_action_shutdown_disabled(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        mock_dev = MagicMock()
        mock_dev.id = 1
        mock_dev.name = "Server"
        mock_dev.shutdown_enabled = False
        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_dev
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._action_shutdown(100, 1)
        assert "未启用" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_cmd_logs_with_entries(self):
        from backend.app.services.telegram_bot import TelegramBot
        from datetime import datetime
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        mock_log = MagicMock()
        mock_log.result = "success"
        mock_log.action = "wake"
        mock_log.detail = "WOL sent to device"
        mock_log.created_at = datetime(2026, 6, 6, 10, 0, 0)
        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_log]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._cmd_logs(100)
        assert "日志" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_cmd_groups_with_groups(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        mock_group = MagicMock()
        mock_group.id = 1
        mock_group.name = "Office"
        mock_dev = MagicMock()
        mock_dev.is_online = True
        mock_dev.name = "PC1"
        mock_dev.ip = "10.0.0.1"

        with patch("backend.app.services.telegram_bot.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result_groups = MagicMock()
            mock_result_groups.scalars.return_value.all.return_value = [mock_group]
            mock_result_devs = MagicMock()
            mock_result_devs.scalars.return_value.all.return_value = [mock_dev]
            mock_db.execute = AsyncMock(side_effect=[mock_result_groups, mock_result_devs])
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await bot._cmd_groups(100)
        bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_bot_cmd_scan_success(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        mock_devices = [{"ip": "10.0.0.1", "mac": "AA:BB:CC:DD:EE:01", "hostname": "server"}]
        with patch("backend.app.services.scanner.scan_lan", new_callable=AsyncMock, return_value=mock_devices):
            await bot._cmd_scan(100)
        assert bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_bot_cmd_scan_running(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        with patch("backend.app.services.scanner.scan_lan", new_callable=AsyncMock,
                   side_effect=RuntimeError("scan running")):
            await bot._cmd_scan(100)
        assert "扫描正在进行中" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_cmd_scan_empty(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.send_message = AsyncMock()
        with patch("backend.app.services.scanner.scan_lan", new_callable=AsyncMock, return_value=[]):
            await bot._cmd_scan(100)
        assert "未发现" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_bot_handle_update_not_allowed(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [111])
        bot.send_message = AsyncMock()
        update = {"message": {"text": "/start", "chat": {"id": 999}}}
        await bot.handle_update(update)
        bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_handle_callback_not_allowed(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [111])
        bot.answer_callback = AsyncMock()
        update = {
            "callback_query": {
                "id": "cb",
                "message": {"chat": {"id": 999}},
                "data": "devices",
            }
        }
        await bot.handle_update(update)
        bot.answer_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_handle_callback_groups(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.answer_callback = AsyncMock()
        bot._cmd_groups = AsyncMock()
        update = {
            "callback_query": {
                "id": "cb",
                "message": {"chat": {"id": 100}},
                "data": "groups",
            }
        }
        await bot.handle_update(update)
        bot._cmd_groups.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_handle_callback_logs(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.answer_callback = AsyncMock()
        bot._cmd_logs = AsyncMock()
        update = {
            "callback_query": {
                "id": "cb",
                "message": {"chat": {"id": 100}},
                "data": "logs",
            }
        }
        await bot.handle_update(update)
        bot._cmd_logs.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_handle_callback_scan(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        bot.answer_callback = AsyncMock()
        bot._cmd_scan = AsyncMock()
        update = {
            "callback_query": {
                "id": "cb",
                "message": {"chat": {"id": 100}},
                "data": "scan",
            }
        }
        await bot.handle_update(update)
        bot._cmd_scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_ensure_client(self):
        from backend.app.services.telegram_bot import TelegramBot
        bot = TelegramBot("token", [])
        with patch("backend.app.services.proxy.get_proxy_config", new_callable=AsyncMock, return_value={"proxy_enabled": False}):
            with patch("backend.app.services.proxy.build_proxy_url", return_value=None):
                await bot._ensure_client()
                assert bot.client is not None
                await bot.close()

    @pytest.mark.asyncio
    async def test_bot_loop_missing_token(self):
        from backend.app.services.telegram_bot import _bot_loop, _status
        _status.clear()
        await _bot_loop(99, {"bot_token": ""})
        assert _status.get(99) == "disconnected"
        _status.clear()


# ============ SCAN ROUTER ============

class TestScanRouter:
    def test_scan_start(self, client, auth_headers):
        mock_devices = [
            {"ip": "10.0.0.1", "mac": "AA:BB:CC:DD:EE:01", "hostname": "macbook-pro"},
            {"ip": "10.0.0.2", "mac": "AA:BB:CC:DD:EE:02", "hostname": "iphone-user"},
            {"ip": "10.0.0.3", "mac": "AA:BB:CC:DD:EE:03", "hostname": "android-device"},
            {"ip": "10.0.0.4", "mac": "AA:BB:CC:DD:EE:04", "hostname": "server-01"},
        ]
        with patch("backend.app.services.scanner.scan_lan", new_callable=AsyncMock, return_value=mock_devices):
            resp = client.post("/api/scan/start", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["devices"]) == 4
            types = [d["guessed_type"] for d in data["devices"]]
            assert "macos" in types
            assert "iphone" in types
            assert "android" in types

    def test_scan_already_running(self, client, auth_headers):
        with patch("backend.app.services.scanner.scan_lan", new_callable=AsyncMock,
                   side_effect=RuntimeError("scan_already_running")):
            resp = client.post("/api/scan/start", headers=auth_headers)
            assert resp.status_code == 409


# ============ SCHEDULER SERVICE ============

class TestSchedulerService:
    @pytest.mark.asyncio
    async def test_execute_task_wake(self):
        from backend.app.services.scheduler import _execute_task
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.name = "Server"
        mock_task_obj = MagicMock()

        with patch("backend.app.services.scheduler.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.side_effect = [mock_device, mock_task_obj]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.commit = AsyncMock()
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock, return_value=(True, "OK")):
                with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                    with patch("backend.app.services.ping_monitor.register_pending_check"):
                        with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                            await _execute_task(1, 1, "wake")

    @pytest.mark.asyncio
    async def test_execute_task_shutdown(self):
        from backend.app.services.scheduler import _execute_task
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.ip = "10.0.0.1"
        mock_device.mac = "AA:BB:CC:DD:EE:01"
        mock_device.name = "Server"
        mock_device.shutdown_enabled = True
        mock_device.shutdown_user = "root"
        mock_device.shutdown_password_enc = "enc"
        mock_device.shutdown_auth_type = "password"
        mock_device.shutdown_key_enc = ""
        mock_device.device_type = "linux"
        mock_task_obj = MagicMock()

        with patch("backend.app.services.scheduler.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.side_effect = [mock_device, mock_task_obj]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.commit = AsyncMock()
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db

            with patch("backend.app.services.shutdown.send_shutdown", new_callable=AsyncMock, return_value=(True, "OK")):
                with patch("backend.app.crypto.decrypt", return_value="pass"):
                    with patch("backend.app.services.log_writer.write_log", new_callable=AsyncMock):
                        with patch("backend.app.services.ping_monitor.register_pending_check"):
                            with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
                                await _execute_task(1, 1, "shutdown")

    @pytest.mark.asyncio
    async def test_execute_task_device_not_found(self):
        from backend.app.services.scheduler import _execute_task
        with patch("backend.app.services.scheduler.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_db
            await _execute_task(999, 999, "wake")

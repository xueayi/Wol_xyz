"""
Coverage booster tests — exercises routes that are otherwise uncovered:
auth, groups, logs, dashboard, schedules, devices CRUD.
"""
import pytest


class TestAuthRouter:
    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_wrong_username(self, client):
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "admin"})
        assert resp.status_code == 401

    def test_get_me(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "admin"

    def test_get_me_without_auth(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_change_password_wrong_current(self, client, auth_headers):
        resp = client.put("/api/auth/password", json={
            "current_password": "wrongcurrent",
            "new_password": "newpass",
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_change_password_and_revert(self, client, auth_headers):
        """Change password then revert so subsequent tests are unaffected."""
        resp = client.put("/api/auth/password", json={
            "current_password": "admin",
            "new_password": "newpass123",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        resp2 = client.post("/api/auth/login", json={"username": "admin", "password": "newpass123"})
        assert resp2.status_code == 200
        new_token = resp2.json()["access_token"]
        # Revert password
        resp3 = client.put("/api/auth/password", json={
            "current_password": "newpass123",
            "new_password": "admin",
        }, headers={"Authorization": f"Bearer {new_token}"})
        assert resp3.status_code == 200

    def test_change_username(self, client, auth_headers):
        resp = client.put("/api/auth/username", json={
            "password": "admin",
            "new_username": "superadmin",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "access_token" in resp.json()
        new_token = resp.json()["access_token"]
        # Revert username
        client.put("/api/auth/username", json={
            "password": "admin",
            "new_username": "admin",
        }, headers={"Authorization": f"Bearer {new_token}"})


class TestGroupsRouter:
    def test_create_group(self, client, auth_headers):
        resp = client.post("/api/groups", json={"name": "Office"}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Office"
        assert data["device_count"] == 0

    def test_list_groups(self, client, auth_headers):
        client.post("/api/groups", json={"name": "Home"}, headers=auth_headers)
        resp = client.get("/api/groups", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_update_group(self, client, auth_headers):
        resp = client.post("/api/groups", json={"name": "Old Name"}, headers=auth_headers)
        group_id = resp.json()["id"]
        resp = client.put(f"/api/groups/{group_id}", json={"name": "New Name"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_nonexistent_group(self, client, auth_headers):
        resp = client.put("/api/groups/9999", json={"name": "X"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_group(self, client, auth_headers):
        resp = client.post("/api/groups", json={"name": "ToDelete"}, headers=auth_headers)
        group_id = resp.json()["id"]
        resp = client.delete(f"/api/groups/{group_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_group(self, client, auth_headers):
        resp = client.delete("/api/groups/9999", headers=auth_headers)
        assert resp.status_code == 404

    def test_list_groups_with_devices(self, client, auth_headers, seeded_devices):
        resp = client.get("/api/groups/with-devices", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestLogsRouter:
    def test_list_logs_empty(self, client, auth_headers):
        resp = client.get("/api/logs", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_logs_after_operation(self, client, auth_headers, seeded_devices, virtual_pool):
        device_id = seeded_devices[0]["id"]
        client.post(f"/api/devices/{device_id}/wake", headers=auth_headers)
        resp = client.get("/api/logs", headers=auth_headers)
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) >= 1
        assert logs[0]["action"] == "wake"

    def test_list_logs_filter_by_device(self, client, auth_headers, seeded_devices, virtual_pool):
        device_id = seeded_devices[0]["id"]
        client.post(f"/api/devices/{device_id}/wake", headers=auth_headers)
        resp = client.get(f"/api/logs?device_id={device_id}", headers=auth_headers)
        assert resp.status_code == 200
        for log in resp.json():
            assert log["device_id"] == device_id

    def test_list_logs_filter_by_action(self, client, auth_headers, seeded_devices, virtual_pool):
        device_id = seeded_devices[0]["id"]
        client.post(f"/api/devices/{device_id}/wake", headers=auth_headers)
        resp = client.get("/api/logs?action=wake", headers=auth_headers)
        assert resp.status_code == 200
        for log in resp.json():
            assert log["action"] == "wake"

    def test_log_count(self, client, auth_headers):
        resp = client.get("/api/logs/count", headers=auth_headers)
        assert resp.status_code == 200
        assert "count" in resp.json()


class TestDashboardRouter:
    def test_get_stats(self, client, auth_headers, seeded_devices):
        resp = client.get("/api/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_devices" in data
        assert "online_devices" in data
        assert "version" in data
        assert data["total_devices"] >= 3


class TestDevicesCRUD:
    def test_create_device(self, client, auth_headers):
        resp = client.post("/api/devices", json={
            "name": "Test PC",
            "ip": "10.0.0.1",
            "mac": "11:22:33:44:55:66",
            "device_type": "linux",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test PC"
        assert data["mac"] == "11:22:33:44:55:66"

    def test_list_devices(self, client, auth_headers, seeded_devices):
        resp = client.get("/api/devices", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    def test_list_devices_filter_by_group(self, client, auth_headers):
        g = client.post("/api/groups", json={"name": "FilterGroup"}, headers=auth_headers).json()
        client.post("/api/devices", json={
            "name": "Grouped",
            "ip": "10.0.0.50",
            "mac": "AA:AA:AA:AA:AA:AA",
            "group_id": g["id"],
        }, headers=auth_headers)
        resp = client.get(f"/api/devices?group_id={g['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_update_device(self, client, auth_headers, seeded_devices):
        device_id = seeded_devices[0]["id"]
        resp = client.put(f"/api/devices/{device_id}", json={
            "name": "Renamed Server",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Server"

    def test_update_nonexistent_device(self, client, auth_headers):
        resp = client.put("/api/devices/9999", json={"name": "X"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_device(self, client, auth_headers, seeded_devices):
        device_id = seeded_devices[2]["id"]
        resp = client.delete(f"/api/devices/{device_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_device(self, client, auth_headers):
        resp = client.delete("/api/devices/9999", headers=auth_headers)
        assert resp.status_code == 404

    def test_batch_delete(self, client, auth_headers, seeded_devices):
        ids = [seeded_devices[0]["id"], seeded_devices[1]["id"]]
        resp = client.post("/api/devices/batch-delete", json={"ids": ids}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 2

    def test_batch_delete_empty(self, client, auth_headers):
        resp = client.post("/api/devices/batch-delete", json={"ids": []}, headers=auth_headers)
        assert resp.status_code == 400

    def test_batch_move(self, client, auth_headers, seeded_devices):
        g = client.post("/api/groups", json={"name": "Target"}, headers=auth_headers).json()
        ids = [seeded_devices[0]["id"]]
        resp = client.post("/api/devices/batch-move", json={
            "ids": ids, "group_id": g["id"],
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["moved"] == 1


class TestSchedulesRouter:
    def test_create_schedule(self, client, auth_headers, seeded_devices):
        device_id = seeded_devices[0]["id"]
        resp = client.post("/api/schedules", json={
            "name": "Daily Wake",
            "device_id": device_id,
            "action": "wake",
            "cron_expression": "0 7 * * *",
            "enabled": True,
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["action"] == "wake"

    def test_list_schedules(self, client, auth_headers, seeded_devices):
        device_id = seeded_devices[0]["id"]
        client.post("/api/schedules", json={
            "name": "Test Schedule",
            "device_id": device_id,
            "action": "shutdown",
            "cron_expression": "0 22 * * *",
            "enabled": True,
        }, headers=auth_headers)
        resp = client.get("/api/schedules", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_update_schedule(self, client, auth_headers, seeded_devices):
        device_id = seeded_devices[0]["id"]
        resp = client.post("/api/schedules", json={
            "name": "Updatable",
            "device_id": device_id,
            "action": "wake",
            "cron_expression": "0 8 * * *",
            "enabled": True,
        }, headers=auth_headers)
        task_id = resp.json()["id"]
        resp = client.put(f"/api/schedules/{task_id}", json={
            "name": "Updated Name",
            "enabled": False,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["enabled"] is False

    def test_update_nonexistent_schedule(self, client, auth_headers):
        resp = client.put("/api/schedules/9999", json={"name": "X"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_schedule(self, client, auth_headers, seeded_devices):
        device_id = seeded_devices[0]["id"]
        resp = client.post("/api/schedules", json={
            "name": "ToDelete",
            "device_id": device_id,
            "action": "wake",
            "cron_expression": "0 6 * * *",
            "enabled": True,
        }, headers=auth_headers)
        task_id = resp.json()["id"]
        resp = client.delete(f"/api/schedules/{task_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_schedule(self, client, auth_headers):
        resp = client.delete("/api/schedules/9999", headers=auth_headers)
        assert resp.status_code == 404


class TestChannelsRouter:
    def test_create_channel(self, client, auth_headers):
        resp = client.post("/api/channels", json={
            "type": "bark",
            "name": "My Bark",
            "config": {"server_url": "https://api.day.app", "device_key": "test123"},
            "enabled": True,
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["name"] == "My Bark"

    def test_list_channels(self, client, auth_headers):
        client.post("/api/channels", json={
            "type": "bark",
            "name": "List Test",
            "config": {"server_url": "https://x.com", "device_key": "k"},
            "enabled": True,
        }, headers=auth_headers)
        resp = client.get("/api/channels", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_update_channel(self, client, auth_headers):
        resp = client.post("/api/channels", json={
            "type": "bark",
            "name": "Old",
            "config": {"device_key": "x"},
            "enabled": True,
        }, headers=auth_headers)
        ch_id = resp.json()["id"]
        resp = client.put(f"/api/channels/{ch_id}", json={
            "name": "New Name",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_nonexistent_channel(self, client, auth_headers):
        resp = client.put("/api/channels/9999", json={"name": "X"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_channel(self, client, auth_headers):
        resp = client.post("/api/channels", json={
            "type": "bark",
            "name": "Delete Me",
            "config": {},
            "enabled": True,
        }, headers=auth_headers)
        ch_id = resp.json()["id"]
        resp = client.delete(f"/api/channels/{ch_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_channel(self, client, auth_headers):
        resp = client.delete("/api/channels/9999", headers=auth_headers)
        assert resp.status_code == 404


class TestAnnouncementsRouter:
    def test_list_announcements_empty(self, client):
        resp = client.get("/api/announcements")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_announcement(self, client, auth_headers):
        resp = client.post("/api/announcements", json={
            "title": "System Update",
            "content": "Maintenance at 3 AM",
            "type": "info",
            "is_pinned": False,
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["title"] == "System Update"

    def test_update_announcement(self, client, auth_headers):
        resp = client.post("/api/announcements", json={
            "title": "Old Title",
            "content": "Old Content",
            "type": "info",
        }, headers=auth_headers)
        ann_id = resp.json()["id"]
        resp = client.put(f"/api/announcements/{ann_id}", json={
            "title": "New Title",
            "is_pinned": True,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"
        assert resp.json()["is_pinned"] is True

    def test_update_nonexistent_announcement(self, client, auth_headers):
        resp = client.put("/api/announcements/9999", json={"title": "X"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_announcement(self, client, auth_headers):
        resp = client.post("/api/announcements", json={
            "title": "Temp",
            "content": "Temp content",
            "type": "info",
        }, headers=auth_headers)
        ann_id = resp.json()["id"]
        resp = client.delete(f"/api/announcements/{ann_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_announcement(self, client, auth_headers):
        resp = client.delete("/api/announcements/9999", headers=auth_headers)
        assert resp.status_code == 404


class TestTriggersRouter:
    def test_create_http_trigger(self, client, auth_headers):
        resp = client.post("/api/triggers", json={
            "name": "My HTTP API",
            "type": "http_api",
            "enabled": True,
            "config": {"token": "secret-token-123"},
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["type"] == "http_api"

    def test_list_triggers(self, client, auth_headers):
        client.post("/api/triggers", json={
            "name": "List Trigger",
            "type": "http_api",
            "enabled": True,
            "config": {"token": "abc"},
        }, headers=auth_headers)
        resp = client.get("/api/triggers", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_update_trigger(self, client, auth_headers):
        resp = client.post("/api/triggers", json={
            "name": "Old Trigger",
            "type": "http_api",
            "enabled": True,
            "config": {"token": "tok1"},
        }, headers=auth_headers)
        trigger_id = resp.json()["id"]
        resp = client.put(f"/api/triggers/{trigger_id}", json={
            "name": "New Trigger Name",
            "enabled": False,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Trigger Name"

    def test_update_nonexistent_trigger(self, client, auth_headers):
        resp = client.put("/api/triggers/9999", json={"name": "X"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_trigger(self, client, auth_headers):
        resp = client.post("/api/triggers", json={
            "name": "Del Trigger",
            "type": "http_api",
            "enabled": True,
            "config": {"token": "tok-del"},
        }, headers=auth_headers)
        trigger_id = resp.json()["id"]
        resp = client.delete(f"/api/triggers/{trigger_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_trigger(self, client, auth_headers):
        resp = client.delete("/api/triggers/9999", headers=auth_headers)
        assert resp.status_code == 404

    def test_trigger_status(self, client, auth_headers):
        resp = client.get("/api/triggers/status", headers=auth_headers)
        assert resp.status_code == 200

    def test_external_trigger_wake(self, client, auth_headers, seeded_devices):
        client.post("/api/triggers", json={
            "name": "ext",
            "type": "http_api",
            "enabled": True,
            "config": {"token": "ext-tok"},
        }, headers=auth_headers)
        mac = seeded_devices[0]["mac"]
        resp = client.get(f"/api/external/trigger?token=ext-tok&mac={mac}&action=wake")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_external_trigger_shutdown(self, client, auth_headers, seeded_devices, virtual_pool):
        from tests.virtual_device.device_simulator import DeviceState
        client.post("/api/triggers", json={
            "name": "ext2",
            "type": "http_api",
            "enabled": True,
            "config": {"token": "ext-tok-2"},
        }, headers=auth_headers)
        mac = seeded_devices[0]["mac"]
        virtual_pool.get_by_mac(mac).state = DeviceState.ONLINE
        resp = client.get(f"/api/external/trigger?token=ext-tok-2&mac={mac}&action=shutdown")
        assert resp.status_code == 200

    def test_external_trigger_invalid_token(self, client):
        resp = client.get("/api/external/trigger?token=bad&mac=AA:BB:CC:DD:EE:01&action=wake")
        assert resp.status_code == 403


class TestSettingsRouter:
    def test_get_timezone(self, client, auth_headers):
        resp = client.get("/api/settings/timezone", headers=auth_headers)
        assert resp.status_code == 200
        assert "timezone" in resp.json()

    def test_get_proxy(self, client, auth_headers):
        resp = client.get("/api/settings/proxy", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "proxy_enabled" in data

    def test_update_proxy(self, client, auth_headers):
        resp = client.put("/api/settings/proxy", json={
            "proxy_enabled": False,
            "proxy_type": "http",
            "proxy_host": "127.0.0.1",
            "proxy_port": 7890,
            "proxy_username": "",
            "proxy_password": "",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["proxy_host"] == "127.0.0.1"


class TestDevicesKeypair:
    def test_generate_keypair(self, client, auth_headers):
        resp = client.post("/api/devices/generate-keypair", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "private_key" in data
        assert "public_key" in data
        assert data["private_key"].startswith("-----BEGIN OPENSSH PRIVATE KEY-----")


class TestAuthRegenerateSecret:
    def test_regenerate_secret(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("backend.app.routers.auth.DATA_DIR", tmp_path)
        resp = client.post("/api/auth/regenerate-secret", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_regenerate_secret_updates_existing_env(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setattr("backend.app.routers.auth.DATA_DIR", tmp_path)
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=old-key\nOTHER=val\n")
        resp = client.post("/api/auth/regenerate-secret", headers=auth_headers)
        assert resp.status_code == 200
        content = env_file.read_text()
        assert "SECRET_KEY=" in content
        assert "old-key" not in content
        assert "OTHER=val" in content


class TestSettingsProxyTest:
    def test_proxy_test_empty_host(self, client, auth_headers):
        resp = client.post("/api/settings/proxy/test", json={
            "proxy_enabled": True,
            "proxy_type": "http",
            "proxy_host": "",
            "proxy_port": 7890,
            "proxy_username": "",
            "proxy_password": "",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is False


class TestTriggersManagement:
    def test_create_telegram_trigger_with_sync(self, client, auth_headers):
        resp = client.post("/api/triggers", json={
            "name": "TG Bot",
            "type": "telegram",
            "enabled": True,
            "config": {
                "bot_token": "123456:ABC-DEF",
                "allowed_chat_ids": "111,222",
                "sync_notify": True,
            },
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["type"] == "telegram"

    def test_update_telegram_trigger_disable_sync(self, client, auth_headers):
        resp = client.post("/api/triggers", json={
            "name": "TG Bot 2",
            "type": "telegram",
            "enabled": True,
            "config": {
                "bot_token": "123456:XYZ",
                "allowed_chat_ids": "333",
                "sync_notify": True,
            },
        }, headers=auth_headers)
        trigger_id = resp.json()["id"]
        resp = client.put(f"/api/triggers/{trigger_id}", json={
            "config": {
                "bot_token": "123456:XYZ",
                "allowed_chat_ids": "333",
                "sync_notify": False,
            },
        }, headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_telegram_trigger(self, client, auth_headers):
        resp = client.post("/api/triggers", json={
            "name": "TG Del",
            "type": "telegram",
            "enabled": True,
            "config": {
                "bot_token": "123456:DEL",
                "allowed_chat_ids": "444",
                "sync_notify": True,
            },
        }, headers=auth_headers)
        trigger_id = resp.json()["id"]
        resp = client.delete(f"/api/triggers/{trigger_id}", headers=auth_headers)
        assert resp.status_code == 204


class TestChannelTest:
    def test_channel_test_sends_notification(self, client, auth_headers):
        resp = client.post("/api/channels", json={
            "type": "bark",
            "name": "Test Channel",
            "config": {"server_url": "https://bark.example.com", "device_key": "testkey"},
            "enabled": True,
        }, headers=auth_headers)
        ch_id = resp.json()["id"]
        resp = client.post(f"/api/channels/{ch_id}/test", headers=auth_headers)
        assert resp.status_code == 200
        assert "success" in resp.json()

    def test_channel_test_nonexistent(self, client, auth_headers):
        resp = client.post("/api/channels/9999/test", headers=auth_headers)
        assert resp.status_code == 404

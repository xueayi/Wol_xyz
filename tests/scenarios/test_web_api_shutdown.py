import pytest


@pytest.mark.web_api
class TestWebApiShutdown:
    def test_shutdown_online_device_succeeds(self, client, auth_headers, seeded_devices, virtual_pool):
        device_id = seeded_devices[1]["id"]  # Windows, online
        resp = client.post(f"/api/devices/{device_id}/shutdown", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        dev = virtual_pool.get_by_mac("AA:BB:CC:DD:EE:02")
        assert dev.state.value == "offline"

    def test_shutdown_offline_device_fails(self, client, auth_headers, seeded_devices, virtual_pool):
        device_id = seeded_devices[0]["id"]  # Linux, offline
        resp = client.post(f"/api/devices/{device_id}/shutdown", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    def test_shutdown_nonexistent_device(self, client, auth_headers):
        resp = client.post("/api/devices/9999/shutdown", headers=auth_headers)
        assert resp.status_code == 404

    def test_shutdown_without_auth(self, client, seeded_devices):
        device_id = seeded_devices[1]["id"]
        resp = client.post(f"/api/devices/{device_id}/shutdown")
        assert resp.status_code == 401

    def test_shutdown_disabled_device(self, client, auth_headers):
        resp = client.post("/api/devices", json={
            "name": "NAS",
            "ip": "192.168.1.200",
            "mac": "FF:FF:FF:FF:FF:01",
            "device_type": "linux",
            "shutdown_enabled": False,
            "shutdown_user": "",
            "shutdown_password": "",
        }, headers=auth_headers)
        device_id = resp.json()["id"]
        resp = client.post(f"/api/devices/{device_id}/shutdown", headers=auth_headers)
        assert resp.status_code == 400
        assert "未启用" in resp.json()["detail"]

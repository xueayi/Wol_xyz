import pytest


@pytest.mark.web_api
class TestWebApiWake:
    def test_wake_offline_device_succeeds(self, client, auth_headers, seeded_devices, virtual_pool):
        device_id = seeded_devices[0]["id"]  # Linux, offline
        resp = client.post(f"/api/devices/{device_id}/wake", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        dev = virtual_pool.get_by_mac("AA:BB:CC:DD:EE:01")
        assert dev.state.value == "online"

    def test_wake_already_online_device(self, client, auth_headers, seeded_devices, virtual_pool):
        device_id = seeded_devices[1]["id"]  # Windows, online
        resp = client.post(f"/api/devices/{device_id}/wake", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_wake_nonexistent_device(self, client, auth_headers):
        resp = client.post("/api/devices/9999/wake", headers=auth_headers)
        assert resp.status_code == 404

    def test_wake_without_auth(self, client, seeded_devices):
        device_id = seeded_devices[0]["id"]
        resp = client.post(f"/api/devices/{device_id}/wake")
        assert resp.status_code == 401

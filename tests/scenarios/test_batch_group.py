import pytest
from tests.virtual_device.device_simulator import DeviceState


@pytest.mark.multi_device
class TestBatchGroupOperations:
    """Test batch wake/shutdown by device IDs and by group_id."""

    @pytest.fixture
    def group_and_devices(self, client, auth_headers, virtual_pool):
        """Create a group with devices assigned to it."""
        resp = client.post("/api/groups", json={"name": "Server Room"}, headers=auth_headers)
        assert resp.status_code == 201
        group_id = resp.json()["id"]

        devices_data = [
            {
                "name": "Linux Server",
                "ip": "192.168.1.100",
                "mac": "AA:BB:CC:DD:EE:01",
                "device_type": "linux",
                "group_id": group_id,
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
                "group_id": group_id,
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
                "group_id": group_id,
                "shutdown_enabled": True,
                "shutdown_user": "user",
                "shutdown_password": "test123",
                "shutdown_auth_type": "password",
            },
        ]
        created = []
        for d in devices_data:
            resp = client.post("/api/devices", json=d, headers=auth_headers)
            assert resp.status_code == 201, resp.text
            created.append(resp.json())
        return {"group_id": group_id, "devices": created}

    def test_batch_wake_by_group_id(self, client, auth_headers, group_and_devices, virtual_pool):
        """Wake all devices in a group."""
        group_id = group_and_devices["group_id"]
        resp = client.post("/api/devices/batch-wake", json={
            "group_id": group_id,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        for r in data["results"]:
            assert r["success"] is True
        for mac in ["AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02", "AA:BB:CC:DD:EE:03"]:
            assert virtual_pool.get_by_mac(mac).state == DeviceState.ONLINE

    def test_batch_shutdown_by_group_id(self, client, auth_headers, group_and_devices, virtual_pool):
        """Shutdown all devices in a group."""
        group_id = group_and_devices["group_id"]
        resp = client.post("/api/devices/batch-shutdown", json={
            "group_id": group_id,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        online_results = [r for r in data["results"] if r["success"]]
        assert len(online_results) == 2  # Windows + macOS were online

    def test_batch_wake_by_ids(self, client, auth_headers, group_and_devices, virtual_pool):
        """Wake specific devices by ID list."""
        devices = group_and_devices["devices"]
        ids = [devices[0]["id"], devices[2]["id"]]
        resp = client.post("/api/devices/batch-wake", json={
            "ids": ids,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(r["success"] for r in data["results"])

    def test_batch_shutdown_by_ids(self, client, auth_headers, group_and_devices, virtual_pool):
        """Shutdown specific devices by ID list."""
        devices = group_and_devices["devices"]
        ids = [devices[1]["id"], devices[2]["id"]]  # Windows + macOS (online)
        resp = client.post("/api/devices/batch-shutdown", json={
            "ids": ids,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(r["success"] for r in data["results"])
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:02").state == DeviceState.OFFLINE
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:03").state == DeviceState.OFFLINE

    def test_batch_wake_no_params_returns_400(self, client, auth_headers, group_and_devices):
        """Must provide either ids or group_id."""
        resp = client.post("/api/devices/batch-wake", json={}, headers=auth_headers)
        assert resp.status_code == 400

    def test_batch_shutdown_no_params_returns_400(self, client, auth_headers, group_and_devices):
        """Must provide either ids or group_id."""
        resp = client.post("/api/devices/batch-shutdown", json={}, headers=auth_headers)
        assert resp.status_code == 400

    def test_batch_wake_empty_group_returns_404(self, client, auth_headers):
        """Empty group returns 404."""
        resp = client.post("/api/groups", json={"name": "Empty Group"}, headers=auth_headers)
        group_id = resp.json()["id"]
        resp = client.post("/api/devices/batch-wake", json={
            "group_id": group_id,
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_batch_shutdown_skips_disabled_devices(self, client, auth_headers, virtual_pool):
        """Devices with shutdown_enabled=False are skipped gracefully."""
        resp = client.post("/api/devices", json={
            "name": "NAS No Shutdown",
            "ip": "192.168.1.200",
            "mac": "FF:FF:FF:FF:FF:01",
            "device_type": "linux",
            "shutdown_enabled": False,
            "shutdown_user": "",
            "shutdown_password": "",
        }, headers=auth_headers)
        device_id = resp.json()["id"]
        resp = client.post("/api/devices/batch-shutdown", json={
            "ids": [device_id],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["success"] is False
        assert "未启用" in data["results"][0]["detail"]

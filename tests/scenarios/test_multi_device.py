import pytest
from tests.virtual_device.device_simulator import DeviceState


@pytest.mark.multi_device
class TestMultiDevice:
    def test_wake_multiple_devices(self, client, auth_headers, seeded_devices, virtual_pool):
        for dev_data in seeded_devices:
            resp = client.post(f"/api/devices/{dev_data['id']}/wake", headers=auth_headers)
            assert resp.status_code == 200
        for mac in ["AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02", "AA:BB:CC:DD:EE:03"]:
            assert virtual_pool.get_by_mac(mac).state == DeviceState.ONLINE

    def test_shutdown_multiple_devices(self, client, auth_headers, seeded_devices, virtual_pool):
        for dev_data in seeded_devices[1:]:
            resp = client.post(f"/api/devices/{dev_data['id']}/shutdown", headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json()["success"] is True
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:02").state == DeviceState.OFFLINE
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:03").state == DeviceState.OFFLINE

    def test_mixed_operations(self, client, auth_headers, seeded_devices, virtual_pool):
        wake_id = seeded_devices[0]["id"]
        shutdown_id = seeded_devices[1]["id"]
        resp1 = client.post(f"/api/devices/{wake_id}/wake", headers=auth_headers)
        resp2 = client.post(f"/api/devices/{shutdown_id}/shutdown", headers=auth_headers)
        assert resp1.json()["success"] is True
        assert resp2.json()["success"] is True
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:01").state == DeviceState.ONLINE
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:02").state == DeviceState.OFFLINE

    def test_external_trigger_multiple_devices(self, client, auth_headers, seeded_devices, virtual_pool):
        client.post("/api/triggers", json={
            "name": "Batch Trigger",
            "type": "http_api",
            "enabled": True,
            "config": {"token": "batch-token-xyz"},
        }, headers=auth_headers)
        resp1 = client.get("/api/external/trigger", params={
            "token": "batch-token-xyz",
            "mac": "AA:BB:CC:DD:EE:01",
            "action": "wake",
        })
        resp2 = client.get("/api/external/trigger", params={
            "token": "batch-token-xyz",
            "mac": "AA:BB:CC:DD:EE:02",
            "action": "shutdown",
        })
        assert resp1.json()["success"] is True
        assert resp2.json()["success"] is True

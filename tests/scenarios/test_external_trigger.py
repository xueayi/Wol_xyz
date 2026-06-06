import pytest


@pytest.fixture
def trigger_token(client, auth_headers):
    resp = client.post("/api/triggers", json={
        "name": "Test HTTP Trigger",
        "type": "http_api",
        "enabled": True,
        "config": {"token": "test-trigger-token-abc123"},
    }, headers=auth_headers)
    assert resp.status_code == 201
    return "test-trigger-token-abc123"


@pytest.mark.external_api
class TestExternalTrigger:
    def test_wake_by_mac_with_valid_token(self, client, seeded_devices, trigger_token, virtual_pool):
        resp = client.get("/api/external/trigger", params={
            "token": trigger_token,
            "mac": "AA:BB:CC:DD:EE:01",
            "action": "wake",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:01").state.value == "online"

    def test_shutdown_by_device_id(self, client, seeded_devices, trigger_token, virtual_pool):
        device_id = seeded_devices[1]["id"]
        resp = client.get("/api/external/trigger", params={
            "token": trigger_token,
            "device_id": device_id,
            "action": "shutdown",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:02").state.value == "offline"

    def test_invalid_token_returns_403(self, client, seeded_devices, trigger_token):
        resp = client.get("/api/external/trigger", params={
            "token": "wrong-token",
            "mac": "AA:BB:CC:DD:EE:01",
            "action": "wake",
        })
        assert resp.status_code == 403

    def test_nonexistent_device_returns_404(self, client, trigger_token):
        resp = client.get("/api/external/trigger", params={
            "token": trigger_token,
            "mac": "FF:FF:FF:FF:FF:FF",
            "action": "wake",
        })
        assert resp.status_code == 404

    def test_unsupported_action_returns_400(self, client, seeded_devices, trigger_token):
        resp = client.get("/api/external/trigger", params={
            "token": trigger_token,
            "mac": "AA:BB:CC:DD:EE:01",
            "action": "reboot",
        })
        assert resp.status_code == 400

    def test_post_method_also_works(self, client, seeded_devices, trigger_token, virtual_pool):
        resp = client.post("/api/external/trigger", params={
            "token": trigger_token,
            "mac": "AA:BB:CC:DD:EE:01",
            "action": "wake",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

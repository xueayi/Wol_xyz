import pytest


@pytest.mark.web_api
class TestFixtureSmoke:
    def test_client_fixture_works(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200

    def test_auth_headers_fixture_works(self, auth_headers):
        assert "Authorization" in auth_headers

    def test_seeded_devices_exist(self, client, auth_headers, seeded_devices):
        resp = client.get("/api/devices", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3

    def test_virtual_pool_has_devices(self, virtual_pool):
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:01") is not None
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:02") is not None
        assert virtual_pool.get_by_mac("AA:BB:CC:DD:EE:03") is not None

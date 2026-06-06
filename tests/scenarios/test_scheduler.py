import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.scheduler
class TestSchedulerTrigger:
    @pytest.mark.asyncio
    async def test_execute_task_wake(self, client, auth_headers, seeded_devices):
        from backend.app.services.scheduler import _execute_task
        device_id = seeded_devices[0]["id"]
        with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock) as mock_wol:
            mock_wol.return_value = (True, "WOL sent")
            await _execute_task(1, device_id, "wake")
            mock_wol.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_shutdown(self, client, auth_headers, seeded_devices):
        from backend.app.services.scheduler import _execute_task
        device_id = seeded_devices[1]["id"]
        with patch("backend.app.services.shutdown.send_shutdown", new_callable=AsyncMock) as mock_sd:
            mock_sd.return_value = (True, "Shutdown sent")
            await _execute_task(1, device_id, "shutdown")
            mock_sd.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_device_not_found(self, client, auth_headers, seeded_devices):
        from backend.app.services.scheduler import _execute_task
        await _execute_task(1, 9999, "wake")  # Should not raise

    def test_create_schedule_via_api(self, client, auth_headers, seeded_devices):
        device_id = seeded_devices[0]["id"]
        resp = client.post("/api/schedules", json={
            "name": "Morning Wake",
            "device_id": device_id,
            "action": "wake",
            "cron_expression": "0 8 * * *",
            "enabled": True,
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["action"] == "wake"
        assert data["enabled"] is True

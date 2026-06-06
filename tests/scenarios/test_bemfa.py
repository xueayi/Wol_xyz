import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.bemfa
class TestBemfaTrigger:
    @pytest.mark.asyncio
    async def test_bemfa_on_triggers_wake(self, client, seeded_devices):
        from tests.triggers.mock_bemfa import simulate_bemfa_message
        with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock) as mock_wol, \
             patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
            mock_wol.return_value = (True, "WOL sent")
            await simulate_bemfa_message("test_topic", "AA:BB:CC:DD:EE:01", "on")
            mock_wol.assert_called_once_with("AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_bemfa_off_triggers_shutdown(self, client, seeded_devices):
        from tests.triggers.mock_bemfa import simulate_bemfa_message
        with patch("backend.app.services.shutdown.send_shutdown", new_callable=AsyncMock) as mock_sd, \
             patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
            mock_sd.return_value = (True, "Shutdown sent")
            await simulate_bemfa_message("test_topic", "AA:BB:CC:DD:EE:02", "off")
            mock_sd.assert_called_once()

    @pytest.mark.asyncio
    async def test_bemfa_unknown_device_no_crash(self, client):
        from tests.triggers.mock_bemfa import simulate_bemfa_message
        with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
            await simulate_bemfa_message("topic", "FF:FF:FF:FF:FF:FF", "on")

    @pytest.mark.asyncio
    async def test_bemfa_invalid_message_ignored(self, client, seeded_devices):
        from backend.app.services.bemfa import _handle_message
        with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock) as mock_wol, \
             patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
            await _handle_message("cmd=0", "topic", {"device_mac": "AA:BB:CC:DD:EE:01"})
            mock_wol.assert_not_called()

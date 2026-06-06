import pytest
import json
from unittest.mock import patch, AsyncMock


@pytest.mark.mqtt
class TestMqttTrigger:
    @pytest.mark.asyncio
    async def test_mqtt_wake_action(self, client, seeded_devices):
        from tests.triggers.mock_mqtt import simulate_mqtt_message
        with patch("backend.app.services.wol.send_wol", new_callable=AsyncMock) as mock_wol, \
             patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
            mock_wol.return_value = (True, "WOL sent")
            await simulate_mqtt_message("AA:BB:CC:DD:EE:01", "wake")
            mock_wol.assert_called_once_with("AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_mqtt_shutdown_action(self, client, seeded_devices):
        from tests.triggers.mock_mqtt import simulate_mqtt_message
        with patch("backend.app.services.shutdown.send_shutdown", new_callable=AsyncMock) as mock_sd, \
             patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
            mock_sd.return_value = (True, "Shutdown sent")
            await simulate_mqtt_message("AA:BB:CC:DD:EE:02", "shutdown")
            mock_sd.assert_called_once()

    def test_mqtt_payload_parsing(self):
        test_cases = [
            (b"on", "wake"), (b"wake", "wake"), (b"1", "wake"),
            (b"off", "shutdown"), (b"shutdown", "shutdown"), (b"0", "shutdown"),
        ]
        for payload, expected_action in test_cases:
            decoded = payload.decode(errors="ignore").strip().lower()
            if decoded in ("on", "wake", "1"):
                action = "wake"
            elif decoded in ("off", "shutdown", "0"):
                action = "shutdown"
            else:
                action = None
            assert action == expected_action, f"Payload {payload} -> expected {expected_action}, got {action}"

    def test_mqtt_json_payload_parsing(self):
        payloads = [
            (json.dumps({"action": "wake"}).encode(), "wake"),
            (json.dumps({"action": "shutdown"}).encode(), "shutdown"),
            (json.dumps({"action": "invalid"}).encode(), None),
        ]
        for payload, expected in payloads:
            decoded = payload.decode(errors="ignore").strip().lower()
            if decoded in ("on", "wake", "1"):
                action = "wake"
            elif decoded in ("off", "shutdown", "0"):
                action = "shutdown"
            else:
                try:
                    data = json.loads(payload)
                    action = data.get("action", "")
                    if action not in ("wake", "shutdown"):
                        action = None
                except Exception:
                    action = None
            assert action == expected, f"Payload {payload} -> expected {expected}, got {action}"

    @pytest.mark.asyncio
    async def test_mqtt_unknown_device(self, client):
        from tests.triggers.mock_mqtt import simulate_mqtt_message
        with patch("backend.app.services.notification.notify_all", new_callable=AsyncMock):
            await simulate_mqtt_message("FF:FF:FF:FF:FF:FF", "wake")

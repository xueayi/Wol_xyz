import pytest
from tests.triggers.mock_telegram import make_callback_data


@pytest.mark.telegram
class TestTelegramTrigger:
    def test_callback_data_format(self):
        assert make_callback_data("wake", 1) == "wake:1"
        assert make_callback_data("shutdown", 42) == "shutdown:42"

    def test_telegram_wake_callback_parsing(self, seeded_devices, client):
        device_id = seeded_devices[0]["id"]
        callback_data = make_callback_data("wake", device_id)
        action, dev_id_str = callback_data.split(":")
        assert action == "wake"
        assert int(dev_id_str) == device_id

    def test_telegram_shutdown_callback_parsing(self, seeded_devices, client):
        device_id = seeded_devices[1]["id"]
        callback_data = make_callback_data("shutdown", device_id)
        action, dev_id_str = callback_data.split(":")
        assert action == "shutdown"
        assert int(dev_id_str) == device_id

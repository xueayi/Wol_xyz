import pytest
from tests.virtual_device.device_simulator import (
    DeviceState,
    VirtualDevice,
    VirtualDevicePool,
)


class TestVirtualDevice:
    def test_initial_state_offline(self):
        dev = VirtualDevice(
            mac="AA:BB:CC:DD:EE:01",
            ip="192.168.1.100",
            device_type="linux",
            initial_state=DeviceState.OFFLINE,
        )
        assert dev.state == DeviceState.OFFLINE
        assert dev.get_ping_result() is False

    def test_receive_wol_transitions_to_online(self):
        dev = VirtualDevice(
            mac="AA:BB:CC:DD:EE:01",
            ip="192.168.1.100",
            device_type="linux",
            initial_state=DeviceState.OFFLINE,
        )
        success, msg = dev.receive_wol()
        assert success is True
        assert dev.state == DeviceState.ONLINE
        assert dev.get_ping_result() is True

    def test_receive_shutdown_transitions_to_offline(self):
        dev = VirtualDevice(
            mac="AA:BB:CC:DD:EE:01",
            ip="192.168.1.100",
            device_type="linux",
            initial_state=DeviceState.ONLINE,
        )
        success, msg = dev.receive_shutdown("linux")
        assert success is True
        assert dev.state == DeviceState.OFFLINE
        assert dev.get_ping_result() is False

    def test_wol_when_already_online(self):
        dev = VirtualDevice(
            mac="AA:BB:CC:DD:EE:01",
            ip="192.168.1.100",
            device_type="linux",
            initial_state=DeviceState.ONLINE,
        )
        success, msg = dev.receive_wol()
        assert success is True
        assert dev.state == DeviceState.ONLINE

    def test_shutdown_when_already_offline(self):
        dev = VirtualDevice(
            mac="AA:BB:CC:DD:EE:01",
            ip="192.168.1.100",
            device_type="linux",
            initial_state=DeviceState.OFFLINE,
        )
        success, msg = dev.receive_shutdown("linux")
        assert success is False

    def test_action_log_records_operations(self):
        dev = VirtualDevice(
            mac="AA:BB:CC:DD:EE:01",
            ip="192.168.1.100",
            device_type="linux",
            initial_state=DeviceState.OFFLINE,
        )
        dev.receive_wol()
        dev.receive_shutdown("linux")
        assert len(dev.action_log) == 2
        assert dev.action_log[0]["action"] == "wake"
        assert dev.action_log[1]["action"] == "shutdown"

    def test_reset_clears_state(self):
        dev = VirtualDevice(
            mac="AA:BB:CC:DD:EE:01",
            ip="192.168.1.100",
            device_type="linux",
            initial_state=DeviceState.OFFLINE,
        )
        dev.receive_wol()
        dev.reset()
        assert dev.state == DeviceState.OFFLINE
        assert dev.action_log == []


class TestVirtualDevicePool:
    def test_register_and_get_by_mac(self):
        pool = VirtualDevicePool()
        pool.register("AA:BB:CC:DD:EE:01", "192.168.1.100", "linux", DeviceState.OFFLINE)
        dev = pool.get_by_mac("AA:BB:CC:DD:EE:01")
        assert dev is not None
        assert dev.ip == "192.168.1.100"

    def test_get_by_mac_normalizes(self):
        pool = VirtualDevicePool()
        pool.register("aa:bb:cc:dd:ee:01", "192.168.1.100", "linux", DeviceState.OFFLINE)
        dev = pool.get_by_mac("AA:BB:CC:DD:EE:01")
        assert dev is not None

    def test_get_by_ip(self):
        pool = VirtualDevicePool()
        pool.register("AA:BB:CC:DD:EE:01", "192.168.1.100", "linux", DeviceState.OFFLINE)
        dev = pool.get_by_ip("192.168.1.100")
        assert dev is not None
        assert dev.mac == "AA:BB:CC:DD:EE:01"

    def test_get_nonexistent_returns_none(self):
        pool = VirtualDevicePool()
        assert pool.get_by_mac("FF:FF:FF:FF:FF:FF") is None
        assert pool.get_by_ip("10.0.0.1") is None

    def test_reset_all(self):
        pool = VirtualDevicePool()
        pool.register("AA:BB:CC:DD:EE:01", "192.168.1.100", "linux", DeviceState.OFFLINE)
        pool.get_by_mac("AA:BB:CC:DD:EE:01").receive_wol()
        pool.reset_all()
        dev = pool.get_by_mac("AA:BB:CC:DD:EE:01")
        assert dev.state == DeviceState.OFFLINE

import pytest
from tests.virtual_device.device_simulator import DeviceState, VirtualDevicePool
from tests.virtual_device.wol_interceptor import WolInterceptor
from tests.virtual_device.shutdown_interceptor import ShutdownInterceptor
from tests.virtual_device.ping_simulator import PingSimulator


@pytest.fixture
def pool():
    p = VirtualDevicePool()
    p.register("AA:BB:CC:DD:EE:01", "192.168.1.100", "linux", DeviceState.OFFLINE)
    p.register("AA:BB:CC:DD:EE:02", "192.168.1.101", "windows", DeviceState.ONLINE)
    p.register("AA:BB:CC:DD:EE:03", "192.168.1.102", "macos", DeviceState.ONLINE)
    return p


class TestWolInterceptor:
    @pytest.mark.asyncio
    async def test_send_wol_wakes_device(self, pool):
        interceptor = WolInterceptor(pool)
        success, msg = await interceptor.send_wol("AA:BB:CC:DD:EE:01")
        assert success is True
        assert pool.get_by_mac("AA:BB:CC:DD:EE:01").state == DeviceState.ONLINE

    @pytest.mark.asyncio
    async def test_send_wol_invalid_mac_format(self, pool):
        interceptor = WolInterceptor(pool)
        success, msg = await interceptor.send_wol("INVALID")
        assert success is False
        assert "格式无效" in msg

    @pytest.mark.asyncio
    async def test_send_wol_unknown_mac(self, pool):
        interceptor = WolInterceptor(pool)
        success, msg = await interceptor.send_wol("FF:FF:FF:FF:FF:FF")
        assert success is True


class TestShutdownInterceptor:
    @pytest.mark.asyncio
    async def test_shutdown_online_device(self, pool):
        interceptor = ShutdownInterceptor(pool)
        success, msg = await interceptor.send_shutdown(
            "192.168.1.101", "admin", "password", device_type="windows"
        )
        assert success is True
        assert pool.get_by_mac("AA:BB:CC:DD:EE:02").state == DeviceState.OFFLINE

    @pytest.mark.asyncio
    async def test_shutdown_offline_device(self, pool):
        interceptor = ShutdownInterceptor(pool)
        success, msg = await interceptor.send_shutdown(
            "192.168.1.100", "admin", "password", device_type="linux"
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_shutdown_records_platform(self, pool):
        interceptor = ShutdownInterceptor(pool)
        await interceptor.send_shutdown(
            "192.168.1.102", "admin", "", private_key="key", device_type="macos"
        )
        dev = pool.get_by_mac("AA:BB:CC:DD:EE:03")
        assert dev.action_log[-1]["platform"] == "macos"


class TestPingSimulator:
    @pytest.mark.asyncio
    async def test_ping_online_device(self, pool):
        sim = PingSimulator(pool)
        result = await sim.ping_host("192.168.1.101")
        assert result is True

    @pytest.mark.asyncio
    async def test_ping_offline_device(self, pool):
        sim = PingSimulator(pool)
        result = await sim.ping_host("192.168.1.100")
        assert result is False

    @pytest.mark.asyncio
    async def test_ping_unknown_ip(self, pool):
        sim = PingSimulator(pool)
        result = await sim.ping_host("10.0.0.1")
        assert result is False

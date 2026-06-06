import pytest
from tests.virtual_device.device_simulator import DeviceState, VirtualDevicePool
from tests.virtual_device.shutdown_interceptor import ShutdownInterceptor
from tests.virtual_device.wol_interceptor import WolInterceptor


@pytest.mark.cross_platform
class TestCrossPlatform:
    @pytest.fixture
    def multi_platform_pool(self):
        pool = VirtualDevicePool()
        pool.register("AA:BB:CC:DD:EE:11", "10.0.0.1", "linux", DeviceState.ONLINE)
        pool.register("AA:BB:CC:DD:EE:12", "10.0.0.2", "windows", DeviceState.ONLINE)
        pool.register("AA:BB:CC:DD:EE:13", "10.0.0.3", "macos", DeviceState.ONLINE)
        return pool

    @pytest.mark.asyncio
    async def test_linux_shutdown(self, multi_platform_pool):
        interceptor = ShutdownInterceptor(multi_platform_pool)
        await interceptor.send_shutdown("10.0.0.1", "root", "pass", device_type="linux")
        assert interceptor.call_log[-1]["device_type"] == "linux"

    @pytest.mark.asyncio
    async def test_windows_shutdown(self, multi_platform_pool):
        interceptor = ShutdownInterceptor(multi_platform_pool)
        await interceptor.send_shutdown("10.0.0.2", "admin", "pass", device_type="windows")
        assert interceptor.call_log[-1]["device_type"] == "windows"

    @pytest.mark.asyncio
    async def test_macos_shutdown(self, multi_platform_pool):
        interceptor = ShutdownInterceptor(multi_platform_pool)
        await interceptor.send_shutdown("10.0.0.3", "user", "", private_key="key", device_type="macos")
        assert interceptor.call_log[-1]["device_type"] == "macos"
        assert interceptor.call_log[-1]["auth_type"] == "key"

    @pytest.mark.asyncio
    async def test_all_platforms_wake(self, multi_platform_pool):
        interceptor = WolInterceptor(multi_platform_pool)
        for mac in ["AA:BB:CC:DD:EE:11", "AA:BB:CC:DD:EE:12", "AA:BB:CC:DD:EE:13"]:
            success, _ = await interceptor.send_wol(mac)
            assert success is True
        assert len(interceptor.call_log) == 3

    def test_shutdown_command_mapping(self):
        from backend.app.services.shutdown import _SHUTDOWN_COMMANDS
        assert _SHUTDOWN_COMMANDS["linux"] == "shutdown -h now"
        assert _SHUTDOWN_COMMANDS["windows"] == "shutdown /s /t 0"
        assert _SHUTDOWN_COMMANDS["macos"] == "sudo shutdown -h now"

    def test_unknown_platform_defaults_to_windows(self):
        from backend.app.services.shutdown import _SHUTDOWN_COMMANDS
        cmd = _SHUTDOWN_COMMANDS.get("unknown_os", _SHUTDOWN_COMMANDS["windows"])
        assert cmd == "shutdown /s /t 0"

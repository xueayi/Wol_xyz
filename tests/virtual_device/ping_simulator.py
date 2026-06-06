from .device_simulator import VirtualDevicePool


class PingSimulator:
    def __init__(self, pool: VirtualDevicePool):
        self.pool = pool

    async def ping_host(self, ip: str) -> bool:
        device = self.pool.get_by_ip(ip)
        if device:
            return device.get_ping_result()
        return False

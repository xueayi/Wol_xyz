from typing import Tuple
from .device_simulator import VirtualDevicePool


class WolInterceptor:
    def __init__(self, pool: VirtualDevicePool):
        self.pool = pool
        self.call_log: list[dict] = []

    async def send_wol(
        self, mac: str, broadcast: str = "255.255.255.255", port: int = 9
    ) -> Tuple[bool, str]:
        mac_clean = mac.replace(":", "").replace("-", "").upper()
        if len(mac_clean) != 12:
            return False, f"MAC 地址格式无效: {mac}"

        self.call_log.append({"mac": mac, "broadcast": broadcast, "port": port})

        mac_normalized = ":".join(mac_clean[i:i+2] for i in range(0, 12, 2))
        device = self.pool.get_by_mac(mac_normalized)
        if device:
            device.receive_wol()
            return True, f"已发送魔术包到 {mac}"
        return True, f"已发送魔术包到 {mac}"

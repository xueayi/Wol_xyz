from typing import Tuple, Optional
from .device_simulator import VirtualDevicePool


class ShutdownInterceptor:
    def __init__(self, pool: VirtualDevicePool):
        self.pool = pool
        self.call_log: list[dict] = []

    async def send_shutdown(
        self,
        ip: str,
        user: str,
        password: str = "",
        *,
        private_key: Optional[str] = None,
        device_type: str = "windows",
    ) -> Tuple[bool, str]:
        self.call_log.append({
            "ip": ip, "user": user, "device_type": device_type,
            "auth_type": "key" if private_key else "password",
        })

        device = self.pool.get_by_ip(ip)
        if device:
            success, msg = device.receive_shutdown(device_type)
            return success, msg
        return False, f"Virtual device not found at {ip}"

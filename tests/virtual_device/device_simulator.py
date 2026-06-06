from enum import Enum
from typing import Optional
import time


class DeviceState(Enum):
    OFFLINE = "offline"
    BOOTING = "booting"
    ONLINE = "online"
    SHUTTING_DOWN = "shutting_down"


class VirtualDevice:
    def __init__(
        self,
        mac: str,
        ip: str,
        device_type: str = "linux",
        initial_state: DeviceState = DeviceState.OFFLINE,
    ):
        self.mac = mac.upper().replace("-", ":")
        self.ip = ip
        self.device_type = device_type
        self._initial_state = initial_state
        self.state = initial_state
        self.action_log: list[dict] = []

    def receive_wol(self) -> tuple[bool, str]:
        self.action_log.append({
            "action": "wake",
            "timestamp": time.time(),
            "prev_state": self.state.value,
        })
        if self.state in (DeviceState.OFFLINE, DeviceState.ONLINE, DeviceState.BOOTING):
            self.state = DeviceState.ONLINE
            return True, f"WOL sent to virtual device {self.mac}"
        return True, f"Device {self.mac} already online"

    def receive_shutdown(self, platform: str) -> tuple[bool, str]:
        self.action_log.append({
            "action": "shutdown",
            "timestamp": time.time(),
            "platform": platform,
            "prev_state": self.state.value,
        })
        if self.state in (DeviceState.ONLINE, DeviceState.BOOTING):
            self.state = DeviceState.OFFLINE
            return True, f"Shutdown sent to virtual device {self.ip}"
        return False, f"Device {self.mac} is not online (state: {self.state.value})"

    def get_ping_result(self) -> bool:
        return self.state in (DeviceState.ONLINE, DeviceState.BOOTING)

    def reset(self):
        self.state = self._initial_state
        self.action_log = []


class VirtualDevicePool:
    def __init__(self):
        self.devices: dict[str, VirtualDevice] = {}
        self._ip_index: dict[str, str] = {}

    def register(
        self,
        mac: str,
        ip: str,
        device_type: str = "linux",
        initial_state: DeviceState = DeviceState.OFFLINE,
    ) -> VirtualDevice:
        dev = VirtualDevice(mac, ip, device_type, initial_state)
        self.devices[dev.mac] = dev
        self._ip_index[ip] = dev.mac
        return dev

    def get_by_mac(self, mac: str) -> Optional[VirtualDevice]:
        normalized = mac.upper().replace("-", ":")
        return self.devices.get(normalized)

    def get_by_ip(self, ip: str) -> Optional[VirtualDevice]:
        mac = self._ip_index.get(ip)
        if mac:
            return self.devices.get(mac)
        return None

    def reset_all(self):
        for dev in self.devices.values():
            dev.reset()

    def get_all_logs(self) -> list[dict]:
        logs = []
        for dev in self.devices.values():
            for entry in dev.action_log:
                logs.append({"mac": dev.mac, "ip": dev.ip, **entry})
        return logs

import asyncio
import socket
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _get_local_subnet() -> Optional[str]:
    """Get the primary local IP and derive /24 subnet prefix."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}"
    except Exception:
        return None


async def _send_udp_broadcast(subnet: str):
    """Send UDP packets to all hosts in /24 to populate ARP table."""
    loop = asyncio.get_event_loop()

    def _broadcast():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.01)
        for i in range(1, 255):
            try:
                sock.sendto(b"\x00", (f"{subnet}.{i}", 9))
            except Exception:
                pass
        sock.close()

    await loop.run_in_executor(None, _broadcast)
    await asyncio.sleep(3)


async def _read_arp_table() -> list[dict]:
    """Parse arp -a output."""
    proc = await asyncio.create_subprocess_exec(
        "arp", "-a",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    text = stdout.decode(errors="ignore")

    devices = []
    for line in text.splitlines():
        match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:]+)", line)
        if match:
            ip, mac = match.group(1), match.group(2).upper()
            if mac != "FF:FF:FF:FF:FF:FF" and not mac.startswith("("):
                devices.append({"ip": ip, "mac": mac})
            continue
        # Windows format
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+\w+", line)
        if match:
            ip = match.group(1)
            mac = match.group(2).replace("-", ":").upper()
            if mac != "FF:FF:FF:FF:FF:FF":
                devices.append({"ip": ip, "mac": mac})

    return devices


async def scan_lan() -> list[dict]:
    subnet = _get_local_subnet()
    if not subnet:
        logger.error("Cannot determine local subnet")
        return []

    logger.info("Scanning subnet %s.0/24", subnet)
    await _send_udp_broadcast(subnet)
    devices = await _read_arp_table()

    seen: dict[str, dict] = {}
    for d in devices:
        mac = d["mac"]
        if mac not in seen:
            seen[mac] = d
        else:
            if not seen[mac].get("ip") and d.get("ip"):
                seen[mac] = d
    devices = list(seen.values())

    logger.info("Found %d unique devices", len(devices))
    return devices

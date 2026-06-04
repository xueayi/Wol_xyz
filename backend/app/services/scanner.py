import asyncio
import socket
import logging
import platform
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


def _get_gateway() -> Optional[str]:
    """Get the default gateway IP via system route table or fallback to .1."""
    import subprocess
    system = platform.system()
    try:
        if system == "Darwin" or system == "Linux":
            result = subprocess.run(
                ["route", "-n", "get", "default"] if system == "Darwin" else ["ip", "route", "show", "default"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.splitlines():
                if "gateway" in line:
                    parts = line.split()
                    idx = parts.index("gateway") + 1 if "gateway" in parts else -1
                    if idx > 0 and idx < len(parts):
                        return parts[idx]
                    gw = line.split(":")[-1].strip()
                    if gw:
                        return gw
    except Exception:
        pass
    # Fallback: guess gateway as .1 of local subnet
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        parts = local_ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
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
            ip = match.group(1)
            mac = ":".join(p.zfill(2) for p in match.group(2).split(":")).upper()
            if mac != "FF:FF:FF:FF:FF:FF" and not mac.startswith("("):
                devices.append({"ip": ip, "mac": mac})
            continue
        # Windows format
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+\w+", line)
        if match:
            ip = match.group(1)
            mac = ":".join(p.zfill(2) for p in match.group(2).replace("-", ":").split(":")).upper()
            if mac != "FF:FF:FF:FF:FF:FF":
                devices.append({"ip": ip, "mac": mac})

    return devices


async def _resolve_hostname(ip: str, gateway: str, semaphore: asyncio.Semaphore) -> Optional[str]:
    """Reverse DNS lookup via the gateway (router) to get device hostname."""
    async with semaphore:
        try:
            proc = await asyncio.create_subprocess_exec(
                "nslookup", ip, gateway,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            text = stdout.decode(errors="ignore")
            for line in text.splitlines():
                if "name =" in line or "name=" in line:
                    name = line.split("name")[-1].strip().strip("=").strip().rstrip(".")
                    if name and name != ip and name != "?":
                        if _is_meaningful_hostname(name):
                            return name
        except Exception:
            pass
    return None


def _is_meaningful_hostname(name: str) -> bool:
    """Filter out hostnames that are just MAC addresses or hex strings."""
    cleaned = name.lower().replace("-", "").replace(":", "").replace("_", "")
    if re.fullmatch(r"[0-9a-f]{12}", cleaned):
        return False
    if name.lower() in ("localhost", "unknown", "?"):
        return False
    return True


async def _resolve_hostnames(devices: list[dict], gateway: str):
    """Resolve hostnames for all devices in parallel (max 5 concurrent)."""
    semaphore = asyncio.Semaphore(5)
    tasks = {d["ip"]: asyncio.create_task(_resolve_hostname(d["ip"], gateway, semaphore)) for d in devices}
    if tasks:
        await asyncio.gather(*tasks.values(), return_exceptions=True)
    for d in devices:
        task = tasks.get(d["ip"])
        if task and task.done() and not task.cancelled():
            result = task.result()
            d["hostname"] = result if isinstance(result, str) else ""
        else:
            d["hostname"] = ""


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

    gateway = _get_gateway()
    if gateway:
        logger.info("Resolving hostnames via gateway %s", gateway)
        await _resolve_hostnames(devices, gateway)

    logger.info("Found %d unique devices", len(devices))
    return devices

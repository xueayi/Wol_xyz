import asyncio
import ipaddress
import socket
import logging
import platform
import re
import shutil
from typing import Optional

logger = logging.getLogger(__name__)

DOCKER_IFACE_PREFIXES = ("docker", "br-", "veth", "virbr", "cni", "flannel", "cali")
DOCKER_SUBNETS = [
    ipaddress.ip_network("172.17.0.0/16"),
    ipaddress.ip_network("172.18.0.0/16"),
    ipaddress.ip_network("172.19.0.0/16"),
    ipaddress.ip_network("172.20.0.0/14"),
    ipaddress.ip_network("192.168.0.0/16"),
]


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


def _get_docker_subnets() -> list[ipaddress.IPv4Network]:
    """Detect Docker bridge subnets by reading network interfaces."""
    subnets: list[ipaddress.IPv4Network] = []
    try:
        import subprocess
        if platform.system() != "Linux":
            return subnets
        result = subprocess.run(
            ["ip", "-4", "-o", "addr", "show"],
            capture_output=True, text=True, timeout=3,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            iface = parts[1]
            if any(iface.startswith(p) for p in DOCKER_IFACE_PREFIXES):
                for p in parts:
                    if "/" in p:
                        try:
                            net = ipaddress.ip_network(p, strict=False)
                            subnets.append(net)
                        except ValueError:
                            pass
    except Exception:
        pass
    return subnets


def _is_docker_ip(ip_str: str, docker_nets: list[ipaddress.IPv4Network]) -> bool:
    """Check if an IP belongs to a known Docker/container network."""
    if not docker_nets:
        return False
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in docker_nets)
    except ValueError:
        return False


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
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+\w+", line)
        if match:
            ip = match.group(1)
            mac = ":".join(p.zfill(2) for p in match.group(2).replace("-", ":").split(":")).upper()
            if mac != "FF:FF:FF:FF:FF:FF":
                devices.append({"ip": ip, "mac": mac})

    return devices


async def _resolve_hostname(ip: str, gateway: str, semaphore: asyncio.Semaphore) -> Optional[str]:
    """Try multiple methods to resolve hostname: nslookup, NetBIOS, mDNS, gethostbyaddr."""
    async with semaphore:
        name = await _try_nslookup(ip, gateway)
        if name:
            return name

        name = await _try_netbios(ip)
        if name:
            return name

        name = await _try_mdns(ip)
        if name:
            return name

        name = await _try_gethostbyaddr(ip)
        if name:
            return name

    return None


async def _try_nslookup(ip: str, gateway: str) -> Optional[str]:
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
                if name and name != ip and name != "?" and _is_meaningful_hostname(name):
                    return name
    except Exception:
        pass
    return None


async def _try_netbios(ip: str) -> Optional[str]:
    """NetBIOS name lookup via nmblookup (samba-common)."""
    if not shutil.which("nmblookup"):
        return None
    try:
        proc = await asyncio.create_subprocess_exec(
            "nmblookup", "-A", ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        text = stdout.decode(errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if "<00>" in line and "GROUP" not in line.upper():
                parts = line.split()
                if parts:
                    name = parts[0].strip()
                    if _is_meaningful_hostname(name):
                        return name
    except Exception:
        pass
    return None


async def _try_mdns(ip: str) -> Optional[str]:
    """mDNS reverse lookup via avahi-resolve (Linux) or dns-sd (macOS)."""
    system = platform.system()
    if system == "Linux" and shutil.which("avahi-resolve"):
        try:
            proc = await asyncio.create_subprocess_exec(
                "avahi-resolve", "-a", ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            text = stdout.decode(errors="ignore").strip()
            if "\t" in text:
                name = text.split("\t")[-1].strip().rstrip(".")
                if _is_meaningful_hostname(name):
                    return name
        except Exception:
            pass
    elif system == "Darwin":
        try:
            proc = await asyncio.create_subprocess_exec(
                "dig", "-x", ip, "+short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            text = stdout.decode(errors="ignore").strip()
            if text:
                name = text.splitlines()[0].rstrip(".")
                if _is_meaningful_hostname(name):
                    return name
        except Exception:
            pass
    return None


async def _try_gethostbyaddr(ip: str) -> Optional[str]:
    """Fallback: Python socket reverse DNS."""
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: socket.gethostbyaddr(ip)),
            timeout=3,
        )
        name = result[0]
        if name and name != ip and _is_meaningful_hostname(name):
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
    """Resolve hostnames for all devices in parallel (max 10 concurrent)."""
    semaphore = asyncio.Semaphore(10)
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

    docker_nets = _get_docker_subnets()
    if docker_nets:
        logger.info("Detected Docker subnets to filter: %s", [str(n) for n in docker_nets])

    logger.info("Scanning subnet %s.0/24", subnet)
    await _send_udp_broadcast(subnet)
    devices = await _read_arp_table()

    if docker_nets:
        before = len(devices)
        devices = [d for d in devices if not _is_docker_ip(d["ip"], docker_nets)]
        filtered = before - len(devices)
        if filtered:
            logger.info("Filtered %d Docker/container IPs", filtered)

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

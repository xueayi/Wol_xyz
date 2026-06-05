import asyncio
import ipaddress
import socket
import logging
import platform
import re
import shutil
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)

DOCKER_IFACE_PREFIXES = ("docker", "br-", "veth", "virbr", "cni", "flannel", "cali")

_scan_lock = asyncio.Lock()


def _get_local_ip() -> Optional[str]:
    """Get the local IP on the real LAN interface (not VPN/proxy tunnels)."""
    import subprocess
    system = platform.system()

    # Method 1: parse interface addresses to find a private LAN IP
    try:
        if system == "Darwin":
            for iface in ("en0", "en1"):
                result = subprocess.run(
                    ["ifconfig", iface],
                    capture_output=True, text=True, timeout=3,
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("inet ") and "127.0.0.1" not in line:
                        ip = line.split()[1]
                        if _is_private_ip(ip):
                            return ip
        elif system == "Linux":
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
                    continue
                if iface == "lo":
                    continue
                for p in parts:
                    if "/" in p:
                        ip = p.split("/")[0]
                        if _is_private_ip(ip):
                            return ip
    except Exception:
        pass

    # Method 2: UDP route probe (may return VPN/proxy IP)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def _is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private and ip != "127.0.0.1"
    except ValueError:
        return False


def _get_scan_network() -> Optional[ipaddress.IPv4Network]:
    """Return the network to scan: user-configured CIDR or auto-detected /24."""
    if settings.SCAN_SUBNET:
        try:
            return ipaddress.ip_network(settings.SCAN_SUBNET, strict=False)
        except ValueError:
            logger.error("Invalid SCAN_SUBNET: %s, falling back to auto-detect", settings.SCAN_SUBNET)

    local_ip = _get_local_ip()
    if not local_ip:
        return None
    return ipaddress.ip_network(f"{local_ip}/24", strict=False)


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
    if not docker_nets:
        return False
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in docker_nets)
    except ValueError:
        return False


def _get_gateway() -> Optional[str]:
    import subprocess
    system = platform.system()
    try:
        if system in ("Darwin", "Linux"):
            result = subprocess.run(
                ["route", "-n", "get", "default"] if system == "Darwin" else ["ip", "route", "show", "default"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.splitlines():
                if "gateway" in line:
                    parts = line.split()
                    idx = parts.index("gateway") + 1 if "gateway" in parts else -1
                    if 0 < idx < len(parts):
                        return parts[idx]
                    gw = line.split(":")[-1].strip()
                    if gw:
                        return gw
    except Exception:
        pass
    local_ip = _get_local_ip()
    if local_ip:
        parts = local_ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
    return None


# ---------------------------------------------------------------------------
# UDP probing: multi-round + broadcast to maximize ARP population
# ---------------------------------------------------------------------------

async def _send_probes(network: ipaddress.IPv4Network, rounds: int):
    """Send multiple rounds of UDP probes + subnet broadcast to fill ARP cache."""
    loop = asyncio.get_event_loop()
    hosts = list(network.hosts())

    def _do_round():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.01)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except Exception:
            pass
        bcast = str(network.broadcast_address)
        for host in hosts:
            try:
                sock.sendto(b"\x00", (str(host), 9))
            except Exception:
                pass
        try:
            sock.sendto(b"\x00", (bcast, 9))
        except Exception:
            pass
        try:
            sock.sendto(b"\xff" * 6, (bcast, 7))
        except Exception:
            pass
        sock.close()

    for r in range(rounds):
        await loop.run_in_executor(None, _do_round)
        if r < rounds - 1:
            await asyncio.sleep(0.3)


async def _send_arp_broadcast(network: ipaddress.IPv4Network):
    """Send a raw ARP broadcast on Linux (best-effort, requires CAP_NET_RAW)."""
    if platform.system() != "Linux":
        return
    local_ip = _get_local_ip()
    if not local_ip:
        return
    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        iface = _get_primary_iface()
        if not iface:
            sock.close()
            return
        sock.bind((iface, 0))
        src_mac = sock.getsockname()[4]
        src_ip = socket.inet_aton(local_ip)
        for host in network.hosts():
            dst_ip = socket.inet_aton(str(host))
            arp_frame = (
                b"\xff\xff\xff\xff\xff\xff"  # dst MAC broadcast
                + src_mac                     # src MAC
                + b"\x08\x06"                 # EtherType ARP
                + b"\x00\x01"                 # HW type Ethernet
                + b"\x08\x00"                 # Protocol IPv4
                + b"\x06\x04"                 # HW size, Proto size
                + b"\x00\x01"                 # Opcode: request
                + src_mac + src_ip            # sender
                + b"\x00" * 6 + dst_ip        # target
            )
            try:
                sock.send(arp_frame)
            except Exception:
                pass
        sock.close()
    except (PermissionError, OSError):
        pass


def _get_primary_iface() -> Optional[str]:
    """Get the primary network interface name on Linux."""
    import subprocess
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True, timeout=3,
        )
        for line in result.stdout.splitlines():
            if "dev" in line:
                parts = line.split()
                idx = parts.index("dev") + 1
                if idx < len(parts):
                    return parts[idx]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# ARP table reading with adaptive wait
# ---------------------------------------------------------------------------

async def _read_arp_table() -> list[dict]:
    """Parse arp -a output, returning list of {ip, mac}."""
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
            ip_addr = match.group(1)
            mac = ":".join(p.zfill(2) for p in match.group(2).split(":")).upper()
            if mac != "FF:FF:FF:FF:FF:FF" and not mac.startswith("("):
                devices.append({"ip": ip_addr, "mac": mac})
            continue
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]+)\s+\w+", line)
        if match:
            ip_addr = match.group(1)
            mac = ":".join(p.zfill(2) for p in match.group(2).replace("-", ":").split(":")).upper()
            if mac != "FF:FF:FF:FF:FF:FF":
                devices.append({"ip": ip_addr, "mac": mac})

    return devices


async def _adaptive_arp_wait(network: ipaddress.IPv4Network, timeout: int) -> list[dict]:
    """Poll ARP table until device count stabilizes or timeout is reached.

    If subnet filtering yields zero results but unfiltered ARP has entries,
    falls back to returning all private-IP ARP entries (handles VPN/proxy
    scenarios where detected subnet doesn't match actual LAN).
    """
    stable_count = 0
    prev_count = 0
    deadline = asyncio.get_event_loop().time() + timeout
    all_seen: dict[str, dict] = {}
    all_raw: dict[str, dict] = {}

    while asyncio.get_event_loop().time() < deadline:
        devices = await _read_arp_table()
        for d in devices:
            all_raw[d["mac"]] = d
        net_devices = [d for d in devices
                       if _ip_in_network_safe(d["ip"], network)]
        for d in net_devices:
            all_seen[d["mac"]] = d

        current_count = len(all_seen)
        if current_count > 0 and current_count == prev_count:
            stable_count += 1
        else:
            stable_count = 0
        prev_count = current_count

        if stable_count >= 3:
            logger.debug("ARP table stabilized at %d devices", current_count)
            break

        await asyncio.sleep(0.5)

    if not all_seen and all_raw:
        logger.warning(
            "No devices matched network %s, falling back to all %d ARP entries "
            "(detected subnet may not match actual LAN, consider setting SCAN_SUBNET)",
            network, len(all_raw),
        )
        private_devs = {mac: d for mac, d in all_raw.items() if _is_private_ip(d["ip"])}
        return list(private_devs.values()) if private_devs else list(all_raw.values())

    return list(all_seen.values())


def _ip_in_network_safe(ip_str: str, network: ipaddress.IPv4Network) -> bool:
    try:
        return ipaddress.ip_address(ip_str) in network
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Hostname resolution: concurrent race (first-wins) with unified timeout
# ---------------------------------------------------------------------------

async def _resolve_hostname(ip: str, gateway: str, semaphore: asyncio.Semaphore,
                            total_timeout: int) -> Optional[str]:
    """Race all hostname methods concurrently; return first valid result."""
    async with semaphore:
        methods = [
            _try_nslookup(ip, gateway),
            _try_gethostbyaddr(ip),
        ]
        if shutil.which("nmblookup"):
            methods.append(_try_netbios(ip))
        system = platform.system()
        if system == "Linux" and shutil.which("avahi-resolve"):
            methods.append(_try_mdns_linux(ip))
        elif system == "Darwin":
            methods.append(_try_mdns_darwin(ip))

        tasks = [asyncio.create_task(m) for m in methods]
        start_time = asyncio.get_event_loop().time()
        pending = set(tasks)
        try:
            while pending:
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining = total_timeout - elapsed
                if remaining <= 0:
                    break
                done, pending = await asyncio.wait(
                    pending, timeout=min(remaining, 0.5),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for t in done:
                    if t.exception() is None:
                        result = t.result()
                        if result:
                            for p in pending:
                                p.cancel()
                            return result
        except Exception:
            pass
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()

    return None


async def _try_nslookup(ip: str, gateway: str) -> Optional[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "nslookup", ip, gateway,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
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
    try:
        proc = await asyncio.create_subprocess_exec(
            "nmblookup", "-A", ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
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


async def _try_mdns_linux(ip: str) -> Optional[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "avahi-resolve", "-a", ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
        text = stdout.decode(errors="ignore").strip()
        if "\t" in text:
            name = text.split("\t")[-1].strip().rstrip(".")
            if _is_meaningful_hostname(name):
                return name
    except Exception:
        pass
    return None


async def _try_mdns_darwin(ip: str) -> Optional[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "dig", "-x", ip, "+short",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
        text = stdout.decode(errors="ignore").strip()
        if text:
            name = text.splitlines()[0].rstrip(".")
            if _is_meaningful_hostname(name):
                return name
    except Exception:
        pass
    return None


async def _try_gethostbyaddr(ip: str) -> Optional[str]:
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
    cleaned = name.lower().replace("-", "").replace(":", "").replace("_", "")
    if re.fullmatch(r"[0-9a-f]{12}", cleaned):
        return False
    if name.lower() in ("localhost", "unknown", "?"):
        return False
    return True


async def _resolve_hostnames(devices: list[dict], gateway: str):
    """Resolve hostnames for all devices with concurrent racing."""
    concurrency = settings.SCAN_HOSTNAME_CONCURRENCY
    timeout = settings.SCAN_HOSTNAME_TIMEOUT
    semaphore = asyncio.Semaphore(concurrency)
    tasks = {d["ip"]: asyncio.create_task(
        _resolve_hostname(d["ip"], gateway, semaphore, timeout)
    ) for d in devices}
    if tasks:
        await asyncio.gather(*tasks.values(), return_exceptions=True)
    for d in devices:
        task = tasks.get(d["ip"])
        if task and task.done() and not task.cancelled():
            try:
                result = task.result()
            except Exception:
                result = None
            d["hostname"] = result if isinstance(result, str) else ""
        else:
            d["hostname"] = ""


# ---------------------------------------------------------------------------
# Main scan entry point
# ---------------------------------------------------------------------------

async def scan_lan() -> list[dict]:
    """Scan the local network. Returns list of {ip, mac, hostname}.

    Uses a lock to prevent concurrent scans.
    Raises RuntimeError if a scan is already in progress.
    """
    if _scan_lock.locked():
        raise RuntimeError("scan_already_running")

    async with _scan_lock:
        network = _get_scan_network()
        if not network:
            logger.error("Cannot determine scan network")
            return []

        docker_nets = _get_docker_subnets()
        if docker_nets:
            logger.info("Docker subnets to filter: %s", [str(n) for n in docker_nets])

        host_count = network.num_addresses - 2
        rounds = settings.SCAN_ROUNDS
        logger.info("Scanning %s (%d hosts, %d rounds)", network, host_count, rounds)

        await _send_probes(network, rounds)

        # best-effort raw ARP broadcast on Linux for devices that ignore UDP
        await _send_arp_broadcast(network)

        devices = await _adaptive_arp_wait(network, settings.SCAN_TIMEOUT)

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

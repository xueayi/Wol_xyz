import asyncio
import socket
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


async def send_wol(mac: str, broadcast: str = "255.255.255.255", port: int = 9) -> Tuple[bool, str]:
    try:
        mac_clean = mac.replace(":", "").replace("-", "").upper()
        if len(mac_clean) != 12:
            return False, f"MAC 地址格式无效: {mac}"
        mac_bytes = bytes.fromhex(mac_clean)
        magic = b"\xFF" * 6 + mac_bytes * 16

        def _send():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic, (broadcast, port))
            sock.close()

        await asyncio.get_event_loop().run_in_executor(None, _send)
        msg = f"已发送魔术包到 {mac}"
        logger.info(msg)
        return True, msg
    except Exception as e:
        msg = f"WOL 发送失败: {e}"
        logger.error(msg)
        return False, msg

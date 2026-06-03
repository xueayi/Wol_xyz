import asyncio
import shutil
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


async def send_shutdown(ip: str, user: str, password: str) -> Tuple[bool, str]:
    try:
        has_sshpass = shutil.which("sshpass") is not None
        if has_sshpass and password:
            cmd = [
                "sshpass", "-p", password, "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                "-o", "PreferredAuthentications=password",
                f"{user}@{ip}",
                "shutdown /s /t 0",
            ]
        else:
            cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                f"{user}@{ip}",
                "shutdown /s /t 0",
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

        if proc.returncode == 0:
            msg = f"关机指令已发送到 {ip}"
            logger.info(msg)
            return True, msg
        else:
            err = stderr.decode(errors="ignore").strip()
            msg = f"关机失败 (exit {proc.returncode}): {err}"
            logger.error(msg)
            return False, msg

    except asyncio.TimeoutError:
        return False, f"SSH 连接超时: {ip}"
    except Exception as e:
        msg = f"关机异常: {e}"
        logger.error(msg)
        return False, msg

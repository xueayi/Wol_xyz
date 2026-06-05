import asyncio
import os
import shutil
import logging
import tempfile
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

_SHUTDOWN_COMMANDS = {
    "windows": "shutdown /s /t 0",
    "linux": "shutdown -h now",
    "macos": "sudo shutdown -h now",
}


async def send_shutdown(
    ip: str,
    user: str,
    password: str = "",
    *,
    private_key: Optional[str] = None,
    device_type: str = "windows",
) -> Tuple[bool, str]:
    shutdown_cmd = _SHUTDOWN_COMMANDS.get(device_type, _SHUTDOWN_COMMANDS["windows"])
    key_path: Optional[str] = None

    try:
        env = os.environ.copy()

        if private_key:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix="_key", delete=False, prefix="wol_ssh_"
            )
            tmp.write(private_key)
            tmp.close()
            key_path = tmp.name
            os.chmod(key_path, 0o600)
            cmd = [
                "ssh",
                "-i", key_path,
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                f"{user}@{ip}",
                shutdown_cmd,
            ]
        elif password:
            has_sshpass = shutil.which("sshpass") is not None
            if has_sshpass:
                env["SSHPASS"] = password
                cmd = [
                    "sshpass", "-e", "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=5",
                    "-o", "PreferredAuthentications=password",
                    f"{user}@{ip}",
                    shutdown_cmd,
                ]
            else:
                cmd = [
                    "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=5",
                    f"{user}@{ip}",
                    shutdown_cmd,
                ]
        else:
            cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                f"{user}@{ip}",
                shutdown_cmd,
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
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
    finally:
        if key_path:
            try:
                os.unlink(key_path)
            except OSError:
                pass

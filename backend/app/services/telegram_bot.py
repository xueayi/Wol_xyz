import asyncio
import logging
from typing import Optional

import httpx
from sqlalchemy import select

from ..database import async_session
from ..models.trigger import TriggerSource
from ..models.device import Device

logger = logging.getLogger(__name__)

_bots: dict[int, asyncio.Task] = {}


async def start_telegram_bots():
    async with async_session() as db:
        result = await db.execute(
            select(TriggerSource).where(TriggerSource.type == "telegram", TriggerSource.enabled.is_(True))
        )
        for trigger in result.scalars().all():
            _start_one(trigger.id, trigger.config)


def _start_one(trigger_id: int, config: dict):
    if trigger_id in _bots and not _bots[trigger_id].done():
        _bots[trigger_id].cancel()
    _bots[trigger_id] = asyncio.create_task(_bot_loop(trigger_id, config))


def stop_all():
    for t in _bots.values():
        t.cancel()
    _bots.clear()


class TelegramBot:
    """Lightweight Telegram Bot using HTTP long polling (no external library needed)."""

    def __init__(self, token: str, allowed_chats: list[int]):
        self.token = token
        self.allowed_chats = allowed_chats
        self.base = f"https://api.telegram.org/bot{token}"
        self.client: Optional[httpx.AsyncClient] = None

    async def _request(self, method: str, **kwargs) -> dict:
        if not self.client:
            self.client = httpx.AsyncClient(timeout=60)
        resp = await self.client.post(f"{self.base}/{method}", json=kwargs)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
        return data.get("result", {})

    async def send_message(self, chat_id: int, text: str, reply_markup: Optional[dict] = None, parse_mode: str = "HTML"):
        params = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if reply_markup:
            params["reply_markup"] = reply_markup
        await self._request("sendMessage", **params)

    async def answer_callback(self, callback_id: str, text: str = ""):
        await self._request("answerCallbackQuery", callback_query_id=callback_id, text=text)

    async def get_updates(self, offset: int = 0) -> list:
        return await self._request("getUpdates", offset=offset, timeout=30)

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    def _is_allowed(self, chat_id: int) -> bool:
        return not self.allowed_chats or chat_id in self.allowed_chats

    async def handle_update(self, update: dict):
        if "callback_query" in update:
            cb = update["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            if not self._is_allowed(chat_id):
                return
            await self.answer_callback(cb["id"])
            await self._handle_callback(chat_id, cb["data"])
            return

        msg = update.get("message", {})
        text = msg.get("text", "")
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id or not self._is_allowed(chat_id):
            return

        if text.startswith("/"):
            cmd = text.split()[0].split("@")[0].lower()
            await self._handle_command(chat_id, cmd)

    async def _handle_command(self, chat_id: int, cmd: str):
        handlers = {
            "/start": self._cmd_start,
            "/help": self._cmd_start,
            "/devices": self._cmd_devices,
            "/status": self._cmd_devices,
            "/groups": self._cmd_groups,
            "/logs": self._cmd_logs,
            "/scan": self._cmd_scan,
        }
        handler = handlers.get(cmd, self._cmd_unknown)
        await handler(chat_id)

    async def _cmd_start(self, chat_id: int):
        keyboard = {"inline_keyboard": [
            [{"text": "📱 设备状态", "callback_data": "devices"}, {"text": "📂 设备分组", "callback_data": "groups"}],
            [{"text": "🔍 扫描局域网", "callback_data": "scan"}, {"text": "📋 操作日志", "callback_data": "logs"}],
        ]}
        await self.send_message(chat_id,
            "<b>Wol_xyz</b> — 局域网设备管理\n\n"
            "可用命令：\n"
            "/devices — 查看设备状态\n"
            "/groups — 查看设备分组\n"
            "/scan — 扫描局域网\n"
            "/logs — 最近操作日志\n\n"
            "或使用下方按钮快速操作：",
            reply_markup=keyboard)

    async def _cmd_devices(self, chat_id: int):
        async with async_session() as db:
            result = await db.execute(select(Device).order_by(Device.id))
            devices = result.scalars().all()

        if not devices:
            await self.send_message(chat_id, "暂无设备，请先在 Web 面板中添加。")
            return

        buttons = []
        lines = ["<b>📱 设备列表</b>\n"]
        for d in devices:
            icon = "🟢" if d.is_online else "🔴"
            lines.append(f"{icon} <b>{d.name}</b>  {d.ip}  <code>{d.mac}</code>")
            row = [{"text": f"⚡ 开机 {d.name}", "callback_data": f"wake:{d.id}"}]
            if d.shutdown_enabled:
                row.append({"text": f"🔌 关机 {d.name}", "callback_data": f"shutdown:{d.id}"})
            buttons.append(row)

        buttons.append([{"text": "🔄 刷新状态", "callback_data": "devices"}])
        await self.send_message(chat_id, "\n".join(lines), reply_markup={"inline_keyboard": buttons})

    async def _cmd_groups(self, chat_id: int):
        from ..models.group import DeviceGroup
        async with async_session() as db:
            groups = (await db.execute(select(DeviceGroup).order_by(DeviceGroup.id))).scalars().all()
            if not groups:
                await self.send_message(chat_id, "暂无分组。")
                return

            lines = ["<b>📂 设备分组</b>\n"]
            for g in groups:
                devs = (await db.execute(
                    select(Device).where(Device.group_id == g.id)
                )).scalars().all()
                online = sum(1 for d in devs if d.is_online)
                lines.append(f"<b>{g.name}</b> — {online}/{len(devs)} 在线")
                for d in devs:
                    icon = "🟢" if d.is_online else "🔴"
                    lines.append(f"  {icon} {d.name} ({d.ip})")
                lines.append("")

        await self.send_message(chat_id, "\n".join(lines))

    async def _cmd_logs(self, chat_id: int):
        from ..models.log import OperationLog
        async with async_session() as db:
            result = await db.execute(
                select(OperationLog).order_by(OperationLog.id.desc()).limit(10)
            )
            logs = result.scalars().all()

        if not logs:
            await self.send_message(chat_id, "暂无操作日志。")
            return

        lines = ["<b>📋 最近操作日志</b>\n"]
        for log in logs:
            icon = "✅" if log.status == "success" else "❌"
            time_str = log.created_at.strftime("%m-%d %H:%M")
            lines.append(f"{icon} [{time_str}] {log.action} — {log.detail[:40]}")

        await self.send_message(chat_id, "\n".join(lines))

    async def _cmd_scan(self, chat_id: int):
        await self.send_message(chat_id, "🔍 正在扫描局域网，请稍候...")
        from .scanner import scan_lan
        devices = await scan_lan()
        if not devices:
            await self.send_message(chat_id, "未发现设备。")
            return

        lines = [f"<b>🔍 扫描结果（{len(devices)} 台设备）</b>\n"]
        for d in devices:
            lines.append(f"• {d['ip']}  <code>{d['mac']}</code>")
        await self.send_message(chat_id, "\n".join(lines))

    async def _cmd_unknown(self, chat_id: int):
        await self.send_message(chat_id, "未知命令，发送 /help 查看可用命令。")

    async def _handle_callback(self, chat_id: int, data: str):
        if data == "devices":
            await self._cmd_devices(chat_id)
        elif data == "groups":
            await self._cmd_groups(chat_id)
        elif data == "logs":
            await self._cmd_logs(chat_id)
        elif data == "scan":
            await self._cmd_scan(chat_id)
        elif data.startswith("wake:"):
            await self._action_wake(chat_id, int(data.split(":")[1]))
        elif data.startswith("shutdown:"):
            await self._action_shutdown(chat_id, int(data.split(":")[1]))

    async def _action_wake(self, chat_id: int, device_id: int):
        async with async_session() as db:
            device = (await db.execute(select(Device).where(Device.id == device_id))).scalar_one_or_none()
            if not device:
                await self.send_message(chat_id, "❌ 设备不存在")
                return

            from .wol import send_wol
            from .log_writer import write_log
            ok, detail = await send_wol(device.mac)
            await write_log(db, device.id, "wake", "success" if ok else "failure", detail, "telegram")
            if ok:
                from .ping_monitor import register_pending_check
                register_pending_check(device.id, "wake", device.name)

        icon = "✅" if ok else "❌"
        await self.send_message(chat_id, f"{icon} 开机 <b>{device.name}</b>\n{detail}")
        from .notification import notify_all
        await notify_all(f"Telegram 开机{'成功' if ok else '失败'}", f"设备: {device.name} | {detail}")

    async def _action_shutdown(self, chat_id: int, device_id: int):
        async with async_session() as db:
            device = (await db.execute(select(Device).where(Device.id == device_id))).scalar_one_or_none()
            if not device:
                await self.send_message(chat_id, "❌ 设备不存在")
                return
            if not device.shutdown_enabled:
                await self.send_message(chat_id, f"⚠️ <b>{device.name}</b> 未启用远程关机")
                return

            from .shutdown import send_shutdown
            from ..crypto import decrypt
            from .log_writer import write_log
            pwd = decrypt(device.shutdown_password_enc)
            ok, detail = await send_shutdown(device.ip, device.shutdown_user, pwd)
            await write_log(db, device.id, "shutdown", "success" if ok else "failure", detail, "telegram")
            if ok:
                from .ping_monitor import register_pending_check
                register_pending_check(device.id, "shutdown", device.name)

        icon = "✅" if ok else "❌"
        await self.send_message(chat_id, f"{icon} 关机 <b>{device.name}</b>\n{detail}")
        from .notification import notify_all
        await notify_all(f"Telegram 关机{'成功' if ok else '失败'}", f"设备: {device.name} | {detail}")


async def _bot_loop(trigger_id: int, config: dict):
    token = config.get("bot_token", "")
    if not token:
        logger.error("Telegram trigger %d: missing bot_token", trigger_id)
        return

    allowed_raw = config.get("allowed_chat_ids", "")
    allowed: list[int] = []
    if isinstance(allowed_raw, list):
        allowed = [int(x) for x in allowed_raw]
    elif isinstance(allowed_raw, str) and allowed_raw.strip():
        allowed = [int(x.strip()) for x in allowed_raw.split(",") if x.strip()]

    bot = TelegramBot(token, allowed)
    offset = 0
    logger.info("Telegram bot started for trigger %d", trigger_id)

    try:
        while True:
            try:
                updates = await bot.get_updates(offset=offset)
                for upd in updates:
                    offset = upd["update_id"] + 1
                    try:
                        await bot.handle_update(upd)
                    except Exception as e:
                        logger.error("Telegram handle_update error: %s", e)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("Telegram poll error: %s", e)
                await asyncio.sleep(5)
    finally:
        await bot.close()
        logger.info("Telegram bot stopped for trigger %d", trigger_id)

async def simulate_bemfa_message(topic: str, device_mac: str, msg_type: str):
    from backend.app.services.bemfa import _handle_message
    raw_msg = f"cmd=2&uid=test&topic={topic}&msg={msg_type}"
    await _handle_message(raw_msg, topic, device_mac)

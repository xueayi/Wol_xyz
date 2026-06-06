async def simulate_mqtt_message(device_mac: str, action: str):
    from backend.app.services.mqtt import _handle_mqtt
    await _handle_mqtt(action, {"device_mac": device_mac})

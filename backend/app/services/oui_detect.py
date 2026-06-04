"""
Guess device type from MAC address OUI (first 3 bytes).
Uses a curated list of common manufacturer OUI prefixes.
"""

_APPLE_OUIS = {
    "00:1C:B3", "00:1E:C2", "00:25:00", "00:26:08", "00:26:BB",
    "3C:07:54", "3C:E0:72", "40:33:1A", "44:D8:84", "48:60:5F",
    "4C:32:75", "54:26:96", "58:55:CA", "5C:F7:E6", "60:03:08",
    "64:A2:F9", "68:5B:35", "6C:96:CF", "70:DE:E2", "78:7E:61",
    "7C:D1:C3", "80:49:71", "84:FC:FE", "88:66:A5", "8C:85:90",
    "90:8D:6C", "98:01:A7", "9C:20:7B", "A4:5E:60", "A8:20:66",
    "AC:BC:32", "B0:65:BD", "B8:17:C2", "BC:52:B7", "C0:B6:58",
    "C8:69:CD", "CC:08:8D", "D0:03:4B", "D4:61:9D", "D8:1C:79",
    "DC:A4:CA", "E0:B9:BA", "E4:CE:8F", "E8:06:88", "F0:18:98",
    "F4:5C:89", "F8:E9:4E", "FC:25:3F",
    "0E:E6:C6",
}

_NAS_OUIS = {
    "00:11:32",  # Synology
    "00:08:9B",  # QNAP
    "00:15:B2",  # Buffalo / NAS
}

_ROUTER_OUIS = {
    "00:0C:43", "14:CF:E2", "50:C7:BF", "54:A7:03", "60:32:B1",  # TP-Link
    "A4:2B:B0", "C0:25:E9", "F8:1A:67",  # TP-Link
    "00:14:6C", "00:1E:2A", "04:D9:F5", "2C:FD:A1", "38:D5:47",  # Netgear
    "04:92:26", "0C:9D:92", "10:C3:7B", "1C:87:2C", "2C:FD:A1",  # Asus
    "30:85:A9", "40:16:7E", "50:46:5D", "AC:9E:17", "B0:6E:BF",  # Asus
    "00:18:E7", "14:DD:A9", "28:6C:07", "78:8A:20", "D4:DA:21",  # Xiaomi router
    "58:D9:D5", "7C:94:2A",  # Huawei router
}

_INTEL_OUIS = {
    "00:1E:67", "3C:97:0E", "48:51:B7", "60:6C:66", "68:05:CA",
    "80:86:F2", "A4:C3:F0", "B4:96:91", "DC:1B:A1", "F8:0F:F9",
    "8C:8C:AA", "48:4D:7E", "C8:5B:76",
}

_REALTEK_OUIS = {
    "00:E0:4C", "52:54:00", "28:32:C5",
}

_ANDROID_OUIS = {
    "00:1A:11",  # Google
    "3C:5A:B4", "AC:37:43", "F4:F5:D8",  # Google/Pixel
    "00:09:2D", "78:02:F8",  # Samsung common for phones
}


def guess_device_type(mac: str) -> str:
    """Guess device type from MAC OUI prefix. Returns one of the defined device_type values."""
    normalized = ":".join(p.zfill(2) for p in mac.upper().replace("-", ":").split(":"))
    prefix = normalized[0:8]

    if prefix in _APPLE_OUIS:
        return "macos"

    if prefix in _NAS_OUIS:
        return "nas"

    if prefix in _ROUTER_OUIS:
        return "router"

    if prefix in _ANDROID_OUIS:
        return "android"

    if prefix in _INTEL_OUIS or prefix in _REALTEK_OUIS:
        return "computer"

    return "computer"

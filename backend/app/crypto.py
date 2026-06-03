"""Fernet symmetric encryption for device SSH passwords."""
from cryptography.fernet import Fernet
from .config import settings, DATA_DIR

_KEY_FILE = DATA_DIR / ".fernet_key"


def _load_key() -> bytes:
    if settings.FERNET_KEY:
        return settings.FERNET_KEY.encode()
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes().strip()
    key = Fernet.generate_key()
    _KEY_FILE.write_bytes(key)
    return key


_fernet = Fernet(_load_key())


def encrypt(plain: str) -> str:
    if not plain:
        return ""
    return _fernet.encrypt(plain.encode()).decode()


def decrypt(token: str) -> str:
    if not token:
        return ""
    return _fernet.decrypt(token.encode()).decode()

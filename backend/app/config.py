from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

_version_file = BASE_DIR / "VERSION"
APP_VERSION = _version_file.read_text().strip() if _version_file.exists() else "dev"


class Settings(BaseSettings):
    APP_NAME: str = "Wol_xyz"
    WEB_PORT: int = 39090
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'wol_xyz.db'}"
    SECRET_KEY: str = "wol-xyz-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    PING_INTERVAL: int = 60
    FERNET_KEY: str = ""

    model_config = {"env_prefix": "", "env_file": str(DATA_DIR / ".env"), "extra": "ignore"}


settings = Settings()

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from . import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_add_columns(conn)


async def _migrate_add_columns(conn):
    """Add new columns to existing tables if they don't exist (simple migration)."""
    import sqlalchemy as sa

    migrations = [
        ("devices", "device_type", "VARCHAR(16) DEFAULT 'computer'"),
        ("devices", "shutdown_auth_type", "VARCHAR(16) DEFAULT 'password'"),
        ("devices", "shutdown_key_enc", "VARCHAR(4096) DEFAULT ''"),
    ]
    for table, column, col_def in migrations:
        try:
            await conn.execute(sa.text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
        except Exception:
            pass

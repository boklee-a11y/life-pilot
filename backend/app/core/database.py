import ssl

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Neon DB requires SSL
connect_args = {}
if "neon.tech" in settings.DATABASE_URL or "sslmode" in settings.DATABASE_URL:
    ssl_context = ssl.create_default_context()
    connect_args["ssl"] = ssl_context

# Convert standard postgresql:// to asyncpg format
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
# Strip query params that asyncpg doesn't understand
if "?" in db_url:
    db_url = db_url.split("?")[0]

engine = create_async_engine(db_url, echo=settings.DEBUG, connect_args=connect_args)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Assicurati che l'URL del DB sia corretto per l'async (es. sqlite+aiosqlite://)
# Se settings.DATABASE_URL è sincrono (sqlite://), dobbiamo convertirlo o assumere sia già corretto.
# Per sicurezza, forziamo sqlite+aiosqlite per questo refactor se è sqlite.
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite://") and not db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(
    db_url,
    pool_size=1000,
    max_overflow=2000,
    pool_timeout=5,
    pool_recycle=1800,
    pool_pre_ping=True,
    # check_same_thread=False è necessario per SQLite in async
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)
AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Gestione URL database per aiosqlite e asyncpg
db_url = str(settings.DATABASE_URL).strip()
if "sqlite" in db_url and "aiosqlite" not in db_url:
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")

db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
db_url = db_url.replace("postgres://", "postgresql+asyncpg://")
db_url = db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

# print(f"DEBUG: Modified DB URL: {db_url}")

engine = create_async_engine(
    db_url,
    future=True,
    echo=False,
    # check_same_thread=False è necessario per SQLite in async
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


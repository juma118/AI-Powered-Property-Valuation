from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Ensure pgvector extension exists and create all tables."""    
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:        
            pass
        await conn.run_sync(Base.metadata.create_all)

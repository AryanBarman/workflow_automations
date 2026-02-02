"""
Database connection and session management.
Uses SQLAlchemy 2.0 async patterns with PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# Convert postgresql:// to postgresql+asyncpg:// for async support
DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Phase 1: Add Sync Engine support for LinearExecutor
# This allows mixing async API with sync Executor logic
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SYNC_DATABASE_URL = settings.database_url
sync_engine = create_engine(SYNC_DATABASE_URL, echo=settings.debug)
SessionLocal = sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency for getting database sessions.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

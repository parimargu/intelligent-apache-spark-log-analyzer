"""
Database connection and session management.
Supports SQLite and PostgreSQL.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings


# Create declarative base for ORM models
Base = declarative_base()

settings = get_settings()


def get_database_url(async_mode: bool = False) -> str:
    """Get database URL, converting to async driver if needed."""
    url = settings.database_url
    
    if async_mode:
        if url.startswith("sqlite:"):
            # SQLite async driver
            url = url.replace("sqlite:", "sqlite+aiosqlite:", 1)
        elif url.startswith("postgresql:"):
            # PostgreSQL async driver
            url = url.replace("postgresql:", "postgresql+asyncpg:", 1)
    
    return url


# Synchronous engine (for migrations and simple operations)
def create_sync_engine():
    """Create synchronous database engine."""
    url = get_database_url(async_mode=False)
    
    if "sqlite" in url:
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug
        )
    
    return create_engine(url, echo=settings.debug)


# Asynchronous engine (for FastAPI endpoints)
def create_async_db_engine():
    """Create asynchronous database engine."""
    url = get_database_url(async_mode=True)
    
    if "sqlite" in url:
        return create_async_engine(
            url,
            echo=settings.debug,
            connect_args={"check_same_thread": False}
        )
    
    return create_async_engine(url, echo=settings.debug)


# Create engines
sync_engine = create_sync_engine()
async_engine = create_async_db_engine()

# Session factories
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Session:
    """Get synchronous database session."""
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.rollback()
        raise


@asynccontextmanager
async def async_session_context():
    """Context manager for async sessions outside of FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def init_db() -> None:
    """Initialize database tables."""
    # Import all models to ensure they are registered
    from app.models import log, user, analysis  # noqa: F401
    Base.metadata.create_all(bind=sync_engine)


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()

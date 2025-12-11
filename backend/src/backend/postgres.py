import threading
from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base, Session, sessionmaker

from config import config


# SQLAlchemy metadata with naming conventions
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

Base = declarative_base(metadata=metadata)


class PostgresConnectionSingleton:
    """Singleton class that holds SQLAlchemy engine and session pools."""

    _async_engine: AsyncEngine | None = None
    _sync_engine = None
    _async_session_factory: async_sessionmaker[AsyncSession] | None = None
    _sync_session_factory = None
    _lock = threading.Lock()

    @classmethod
    def get_async_engine(cls) -> AsyncEngine:
        """Get or create the async database engine."""
        if cls._async_engine is None:
            with cls._lock:
                if cls._async_engine is None:
                    cls._initialize_async_engine()
        return cls._async_engine

    @classmethod
    def get_sync_engine(cls):
        """Get or create the sync database engine (for migrations)."""
        if cls._sync_engine is None:
            with cls._lock:
                if cls._sync_engine is None:
                    cls._initialize_sync_engine()
        return cls._sync_engine

    @classmethod
    def get_async_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        """Get or create the async session factory."""
        if cls._async_session_factory is None:
            with cls._lock:
                if cls._async_session_factory is None:
                    engine = cls.get_async_engine()
                    cls._async_session_factory = async_sessionmaker(
                        engine,
                        class_=AsyncSession,
                        expire_on_commit=False,
                    )
        return cls._async_session_factory

    @classmethod
    def get_sync_session_factory(cls):
        """Get or create the sync session factory (for migrations)."""
        if cls._sync_session_factory is None:
            with cls._lock:
                if cls._sync_session_factory is None:
                    engine = cls.get_sync_engine()
                    cls._sync_session_factory = sessionmaker(
                        engine,
                        class_=Session,
                        expire_on_commit=False,
                    )
        return cls._sync_session_factory

    @classmethod
    def _get_database_url(cls, async_driver: bool = True) -> str:
        """
        Build PostgreSQL database URL from configuration.

        Args:
            async_driver: If True, use asyncpg driver. If False, use psycopg2.
        """
        host = config.settings.get("POSTGRES_HOST", "localhost")
        port = config.settings.get("POSTGRES_PORT", 5432)
        user = config.settings.get("POSTGRES_USER", "postgres")
        password = config.settings.get("POSTGRES_PASSWORD", "postgres")
        db = config.settings.get("POSTGRES_DB", "opencp")

        if async_driver:
            # For async SQLAlchemy operations (FastAPI endpoints)
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        else:
            # For sync operations (Alembic migrations)
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

    @classmethod
    def _initialize_async_engine(cls):
        """Initialize the async database engine with connection pooling."""
        database_url = cls._get_database_url(async_driver=True)
        pool_size = int(config.settings.get("POSTGRES_POOL_SIZE", 10))
        max_overflow = int(config.settings.get("POSTGRES_MAX_OVERFLOW", 20))

        cls._async_engine = create_async_engine(
            database_url,
            echo=config.settings.get("DEBUG", False),
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )

    @classmethod
    def _initialize_sync_engine(cls):
        """Initialize the sync database engine (for Alembic migrations)."""
        database_url = cls._get_database_url(async_driver=False)
        pool_size = int(config.settings.get("POSTGRES_POOL_SIZE", 10))
        max_overflow = int(config.settings.get("POSTGRES_MAX_OVERFLOW", 20))

        cls._sync_engine = create_engine(
            database_url,
            echo=config.settings.get("DEBUG", False),
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )

    @classmethod
    async def close(cls):
        """Close database connections (call on app shutdown)."""
        if cls._async_engine:
            await cls._async_engine.dispose()
            cls._async_engine = None
        if cls._sync_engine:
            cls._sync_engine.dispose()
            cls._sync_engine = None


# Convenience functions for getting engine and sessions
POSTGRES_ASYNC_ENGINE = PostgresConnectionSingleton.get_async_engine
POSTGRES_SYNC_ENGINE = PostgresConnectionSingleton.get_sync_engine
POSTGRES_ASYNC_SESSION_FACTORY = PostgresConnectionSingleton.get_async_session_factory
POSTGRES_SYNC_SESSION_FACTORY = PostgresConnectionSingleton.get_sync_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get a database session.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    factory = POSTGRES_ASYNC_SESSION_FACTORY()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

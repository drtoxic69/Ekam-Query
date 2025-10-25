import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings

logger = logging.getLogger(__name__)

try:
    async_engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=0,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

    AsyncSessionFactory = async_sessionmaker(
        bind=async_engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
    )

    logger.info("Async database engine and session factory created successfully.")

except SQLAlchemyError as e:
    logger.error(f"Failed to create database engine. Error: {e}")
    raise RuntimeError(f"Could not initialize database engine: {e}")

import logging
from typing import AsyncGenerator
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.sessions import AsyncSessionFactory

logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to create and yield a database session with
    automatic transaction management (commit-on-success, rollback-on-failure).
    """
    session: AsyncSession = AsyncSessionFactory()

    try:
        yield session
        await session.commit()

    except SQLAlchemyError as sql_exc:
        logger.error(f"Database error during request: {sql_exc}", exc_info=True)

        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred with the database.",
        )

    except Exception as e:
        logger.error(f"Unexpected error during request: {e}", exc_info=True)

        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred.",
        )

    finally:
        await session.close()

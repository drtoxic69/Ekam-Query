import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db_session
from backend.schemas.schema import SchemaResponse
from backend.services.schema_discovery import SchemaDiscoveryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/schema",
    response_model=SchemaResponse,
    summary="Get Discovered Database Schema",
    description="Connects to the configured database and dynamically returns its "
    "discovered schema, including all tables, columns, types, "
    "constraints, and indexes.",
    tags=["Schema"],
)
async def get_database_schema(db: AsyncSession = Depends(get_db_session)):
    """
    Endpoint to trigger the dynamic schema discovery process.

    The database session is injected by the `get_db_session` dependency,
    which also handles transaction management (commit/rollback) and cleanup.
    """
    try:
        logger.info("GET /api/schema endpoint called.")

        discovery_service = SchemaDiscoveryService(db)

        schema_response = await discovery_service.analyze_database()

        # Error Case for empty database
        if not schema_response.tables:
            logger.warning("No tables found in the database. Returning 404.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tables found in the database. "
                "Please ensure the database is not empty.",
            )

        logger.info(f"Successfully discovered {schema_response.total_tables} tables.")

        return schema_response

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(
            f"Failed to get schema due to an unexpected error: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the schema.",
        )

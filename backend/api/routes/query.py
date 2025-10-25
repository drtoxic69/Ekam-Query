import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db_session
from backend.schemas.query import QueryRequest, QueryResponse
from backend.services.query_engine import QueryEngineService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_query_engine_service(
    db: AsyncSession = Depends(get_db_session),
) -> QueryEngineService:
    """Dependency to create a QueryEngineService instance per request."""
    return QueryEngineService(db)


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit a Natural Language Query",
    description="Processes a natural language query by classifying it, "
    "generating SQL against the database, and/or "
    "searching ingested documents.",
    tags=["Query"],
)
async def process_query_endpoint(
    request: QueryRequest,
    service: QueryEngineService = Depends(get_query_engine_service),
):
    """
    Endpoint to handle a user's natural language query.
    """

    logger.info(f"Processing query: {request.query}")

    try:
        response = await service.process_query(request.query)
        return response

    except Exception as e:
        logger.error(f"Failed to process query '{request.query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the query.",
        )

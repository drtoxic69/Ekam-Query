import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db_session
from backend.schemas.query import QueryRequest, QueryResponse
from backend.services.query_engine import QueryEngineService

logger = logging.getLogger(__name__)
router = APIRouter()


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
    request: QueryRequest, db: AsyncSession = Depends(get_db_session)
):
    """
    Endpoint to handle a user's natural language query.
    """

    logger.info(f"Processing query: {request.query}")

    try:
        # 1. Initialize the service with the database session
        service = QueryEngineService(db)

        # 2. Call the service to do all the hard work
        response = await service.process_query(request.query)

        # 3. Return the successful response
        return response

    except Exception as e:
        # 4. Catch any unexpected errors from the service
        logger.error(f"Failed to process query '{request.query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the query.",
        )

import logging
from fastapi import FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from backend.core.config import settings
from backend.db.sessions import AsyncSessionFactory

from backend.api.routes import ingestion, query, schema

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for dynamic NLP query engine for employee data.",
    version="0.1.0",
    # Disable the /docs endpoint in a production environment
    docs_url="/docs" if settings.DATABASE_ECHO else None,
    redoc_url="/redoc" if settings.DATABASE_ECHO else None,
)

logger.info("FastAPI application instance created.")

app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(schema.router, prefix="/api", tags=["Schema"])

logger.info("API routers included.")


@app.get("/", tags=["Health"])
def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": f"Welcome to {settings.PROJECT_NAME} API"}


@app.get("/api/health", tags=["Health"])
async def db_health_check():
    """
    A robust health check endpoint.
    It verifies database connectivity by performing a simple query.

    Why this is robust:
    - It uses its own session to avoid transactional dependencies (like deps.py).
    - It explicitly returns a 503 (Service Unavailable) on failure.
    - It guarantees the session is closed in all cases.
    """
    session: AsyncSession | None = None

    try:
        session = AsyncSessionFactory()

        result = await session.execute(text("SELECT 1"))

        if result.scalar_one() == 1:
            logger.debug("Database health check successful.")
            return {"status": "ok", "database": "connected"}

        raise Exception("Health check query failed to return '1'.")

    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {e}",
        )

    finally:
        if session:
            await session.close()

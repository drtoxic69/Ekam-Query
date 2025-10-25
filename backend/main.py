import logging

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from backend.api.routes import ingestion, query, schema
from backend.core.config import settings
from backend.db.sessions import AsyncSessionFactory

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

origins = [
    "http://localhost",  # Allow general localhost
    "http://localhost:5173",  # Allow Vite default dev server
    "http://127.0.0.1:5173",  # Allow Vite default dev server (alternative)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins allowed to make requests
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

logger.info("FastAPI application instance created.")
logger.info(f"CORS enabled for origins: {origins}")

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

import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.health import DatabaseHealthResponse, HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check operational status of ORVEX API service.",
)
async def get_health() -> HealthResponse:
    """Returns basic service health status."""
    return HealthResponse(
        status="ok",
        service="ORVEX API",
        version="v1",
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Database Health Check",
    description="Check connectivity to the PostgreSQL database.",
)
async def get_db_health(db: AsyncSession = Depends(get_db_session)) -> DatabaseHealthResponse | JSONResponse:
    """Returns database connectivity health status."""
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return DatabaseHealthResponse(
                status="ok",
                database="PostgreSQL",
                connected=True,
                details="Database connection successful",
            )
        raise Exception("Unexpected query result")
    except Exception as exc:
        logger.warning("Database health check failed: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=DatabaseHealthResponse(
                status="error",
                database="PostgreSQL",
                connected=False,
                details=f"Database connection failed: {str(exc)}",
            ).model_dump(),
        )

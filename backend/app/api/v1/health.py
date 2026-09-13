from fastapi import APIRouter, status
from app.schemas.health import HealthResponse

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

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response schema for API health check endpoint."""

    status: str = Field(default="ok", description="Current health status of the API service")
    service: str = Field(default="ORVEX API", description="Name of the service reporting health status")
    version: str = Field(default="v1", description="API version")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "service": "ORVEX API",
                "version": "v1",
            }
        }
    }

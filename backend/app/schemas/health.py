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


class DatabaseHealthResponse(BaseModel):
    """Response schema for Database health check endpoint."""

    status: str = Field(default="ok", description="Database connectivity status ('ok' or 'error')")
    database: str = Field(default="PostgreSQL", description="Database engine name")
    connected: bool = Field(default=True, description="Boolean flag indicating database connection success")
    details: str | None = Field(default=None, description="Optional detail message")

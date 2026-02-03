from pydantic import BaseModel, ConfigDict


class RootResponse(BaseModel):
    """
    Schema for the root endpoint response.
    Provides basic service information without leaking sensitive details.
    """
    service: str
    version: str
    status: str
    documentation_url: str | None = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service": "FastAPI Gateway",
                "version": "0.1.0",
                "status": "operational",
                "documentation_url": "/docs"
            }
        }
    )

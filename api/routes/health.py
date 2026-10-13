"""Health and readiness endpoints."""

from fastapi import APIRouter

from api.database import check_database
from api.models import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health():
    """Check whether the API process is responding."""
    return {
        "status": "ok",
        "service": "fraud-detection-api",
    }


@router.get("/ready", response_model=ReadinessResponse)
def readiness():
    """Check whether the API can access its required database."""
    database_ready = check_database()

    return {
        "status": "ready" if database_ready else "not_ready",
        "database": "ok" if database_ready else "unavailable",
    }
"""Health endpoint for the Smart Greenhouse API."""

from fastapi import APIRouter
from pydantic import BaseModel

from infrastructure.db import check_database

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Reported status of the API process and its database connection."""

    status: str  # "ok" when everything works, "degraded" when the database is down
    db: str  # "ok" or "fail"


@router.get("/health", response_model=HealthResponse, summary="API and database health")
def read_health() -> HealthResponse:
    """Report whether the API is running and whether PostgreSQL answers a query."""
    db_ok = check_database()
    return HealthResponse(status="ok" if db_ok else "degraded", db="ok" if db_ok else "fail")

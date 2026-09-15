"""FastAPI application entry point for the Smart Greenhouse API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from infrastructure.settings import settings
from interfaces.api.health import router as health_router

app = FastAPI(
    title="Smart Greenhouse API",
    version="0.1.0",
    description="Phase 1 skeleton: three-tier smart greenhouse application.",
    docs_url=None,  # Swagger UI disabled on purpose; Scalar is used instead
    redoc_url=None,  # ReDoc disabled as well
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)


@app.get("/", tags=["meta"], summary="API discovery")
def read_root() -> dict[str, str]:
    """Point clients at the API reference and the OpenAPI schema."""
    return {
        "message": "Smart Greenhouse API",
        "api_reference": "/scalar",
        "openapi": "/openapi.json",
    }


@app.get("/scalar", include_in_schema=False)
def scalar_html():
    """Serve the Scalar API reference UI."""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

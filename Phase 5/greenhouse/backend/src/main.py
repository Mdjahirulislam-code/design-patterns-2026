import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from infrastructure.sampler_runner import sampler_loop
from infrastructure.settings import settings

from interfaces.api.health import router as health_router
from interfaces.api.sensors import router as sensors_router
from interfaces.api.devices import router as devices_router
from interfaces.api.locations import router as locations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Phase 5: start the simulation sampler with the API and stop it on shutdown."""
    task = None

    if settings.sampler_enabled:
        task = asyncio.create_task(sampler_loop())

    yield

    if task is not None:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="Smart Greenhouse API",
    version="0.5.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Routers
app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(devices_router)
app.include_router(locations_router)


@app.get("/scalar", include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

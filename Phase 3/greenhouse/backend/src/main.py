from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from infrastructure.settings import settings
from interfaces.api.health import router as health_router
from interfaces.api.sensors import router as sensors_router
from interfaces.api.devices import router as devices_router

app=FastAPI(title="Smart Greenhouse API",version="0.3.0",docs_url=None,redoc_url=None)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(devices_router)

@app.get("/scalar",include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(openapi_url=app.openapi_url,title=app.title)

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.geocode import router as geocode_router
from app.api.route_weather import router as route_weather_router

app = FastAPI(
    title="Route Weather API",
    description="Weather-aware route planning API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "route-weather-api",
        "timestamp": datetime.now(UTC).isoformat(),
        "graphhopper_configured": bool(settings.graphhopper_api_key),
    }


app.include_router(geocode_router)
app.include_router(route_weather_router)

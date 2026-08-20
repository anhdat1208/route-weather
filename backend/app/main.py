from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Route Weather API",
    description="Weather-aware route planning API",
    version="0.1.0",
)

_boot_error: str | None = None

try:
    from app.config import settings
    from app.api.geocode import router as geocode_router
    from app.api.route_weather import router as route_weather_router

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(geocode_router)
    app.include_router(route_weather_router)
except Exception as exc:  # noqa: BLE001 - surface boot failures on Vercel
    import traceback

    _boot_error = traceback.format_exc()
    # Still allow browser calls while debugging boot failures.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/api/health")
async def health_check() -> dict:
    if _boot_error:
        return {
            "status": "error",
            "service": "route-weather-api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "boot_error": _boot_error[-2000:],
        }

    from app.config import settings

    return {
        "status": "ok",
        "service": "route-weather-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graphhopper_configured": bool(settings.graphhopper_api_key),
    }

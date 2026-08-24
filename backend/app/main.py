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
    from app.api.radar import router as radar_router
    from app.api.route_weather import router as route_weather_router
    from app.api.satellite import router as satellite_router
    from app.api.weather_fusion import router as weather_fusion_router

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(geocode_router)
    app.include_router(radar_router)
    app.include_router(satellite_router)
    app.include_router(weather_fusion_router)
    app.include_router(route_weather_router)
    try:
        from app.api.rain_cells import router as rain_cells_router

        app.include_router(rain_cells_router)
    except Exception:  # noqa: BLE001 - Stage 3 must not take down radar/route APIs
        import logging

        logging.getLogger(__name__).exception("Rain-cell router failed to load")
except Exception:  # noqa: BLE001 - surface boot failures on Vercel
    import traceback

    _boot_error = traceback.format_exc()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/api/health")
async def health() -> dict:
    if _boot_error:
        return {
            "status": "error",
            "service": "route-weather-api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "boot_error": _boot_error[-2000:],
            "graphhopper_configured": False,
        }

    from app.config import settings

    return {
        "status": "ok",
        "service": "route-weather-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graphhopper_configured": bool(settings.graphhopper_api_key),
    }


@app.get("/api/debug/weather")
async def debug_weather(lat: float = 10.74, lng: float = 106.69) -> dict:
    """Temporary diagnostics for Open-Meteo connectivity on Vercel."""
    from app.providers.open_meteo import OpenMeteoProvider

    provider = OpenMeteoProvider()
    try:
        snap = await provider.get_forecast_at(lat=lat, lng=lng, time=datetime.now())
        return {
            "ok": True,
            "time": snap.time.isoformat(),
            "temperature_c": snap.temperature_c,
            "precipitation_probability_pct": snap.precipitation_probability_pct,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

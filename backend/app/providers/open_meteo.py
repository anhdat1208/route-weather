from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

from app.config import settings
from app.providers.base import WeatherProvider
from app.providers.errors import ProviderNotConfiguredError, WeatherNotAvailableError
from app.schemas.weather import WeatherSnapshot


def _parse_open_meteo_time(s: str) -> datetime:
    # Open-Meteo typically returns "YYYY-MM-DDTHH:00" in the chosen timezone.
    # Using fromisoformat keeps it naive; we compare it to the naive target hour.
    return datetime.fromisoformat(s)


def _condition_from_weather_code(code: int | None) -> str | None:
    if code is None:
        return None

    # WMO weather interpretation codes (Open-Meteo: "weather_code").
    if code == 0:
        return "Quang"
    if code in (1, 2, 3):
        return "Mây nhẹ"
    if code in (45, 48):
        return "Sương mù"
    if code in (51, 53, 55, 56, 57):
        return "Mưa phùn"
    if code in (61, 63, 65, 66, 67):
        return "Mưa"
    if code in (80, 81, 82):
        return "Mưa rào"
    if code in (85, 86):
        return "Tuyết"
    if code in (95, 96, 99):
        return "Dông"
    return "Khác"


class OpenMeteoProvider(WeatherProvider):
    def __init__(
        self,
        *,
        base_url: str = settings.open_meteo_base_url,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._client = http_client or httpx.AsyncClient(timeout=20.0)
        self._cache: dict[tuple[float, float, datetime], tuple[WeatherSnapshot, float]] = {}

    async def get_forecast_at(self, *, lat: float, lng: float, time: datetime) -> WeatherSnapshot:
        # MVP scope: primarily "Today + custom departure time".
        # Open-Meteo "forecast" should include times within the next couple of days.
        # Strip tzinfo so comparison with naive Open-Meteo times works.
        target_hour = time.replace(minute=0, second=0, microsecond=0, tzinfo=None)
        cache_key = (round(lat, 3), round(lng, 3), target_hour)

        now_ts = datetime.now().timestamp()
        cached = self._cache.get(cache_key)
        if cached:
            snapshot, expires_at = cached
            if now_ts <= expires_at:
                return snapshot

        params: dict[str, Any] = {
            "latitude": lat,
            "longitude": lng,
            "hourly": ",".join(
                [
                    "temperature_2m",
                    "apparent_temperature",
                    "precipitation_probability",
                    "precipitation",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "relative_humidity_2m",
                    "visibility",
                    "weather_code",
                ]
            ),
            "timezone": "Asia/Bangkok",
            "forecast_days": 2,
        }

        url = f"{self._base_url}/forecast"

        resp = await self._client.get(url, params=params)
        if resp.status_code != 200:
            raise WeatherNotAvailableError(f"Open-Meteo failed: {resp.status_code} {resp.text}")

        payload = resp.json()
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            raise WeatherNotAvailableError("Open-Meteo response missing hourly.time")

        # Find exact hour match; if not found, we treat it as unavailable for strictness.
        target_key = target_hour.isoformat(timespec="minutes")
        idx = None
        for i, t in enumerate(times):
            try:
                parsed = _parse_open_meteo_time(t)
            except ValueError:
                continue
            if parsed == target_hour:
                idx = i
                break

        if idx is None:
            logger.warning(
                "Open-Meteo hour mismatch: target=%s, available range=%s..%s (%d entries)",
                target_hour.isoformat(), times[0] if times else "?", times[-1] if times else "?", len(times),
            )
            raise WeatherNotAvailableError("Open-Meteo forecast not available for requested hour.")

        def pick(name: str) -> float | None:
            arr = hourly.get(name)
            if isinstance(arr, list) and idx < len(arr):
                v = arr[idx]
                return float(v) if isinstance(v, (int, float)) else None
            return None

        # visibility is in meters
        visibility_m = pick("visibility")
        visibility_km = visibility_m / 1000.0 if visibility_m is not None else None

        weather_code = pick("weather_code")

        snapshot = WeatherSnapshot(
            time=target_hour,
            weather_code=int(weather_code) if weather_code is not None else None,
            condition=_condition_from_weather_code(int(weather_code)) if weather_code is not None else None,
            temperature_c=pick("temperature_2m"),
            apparent_temperature_c=pick("apparent_temperature"),
            precipitation_probability_pct=pick("precipitation_probability"),
            precipitation_mm=pick("precipitation"),
            wind_speed_kmh=pick("wind_speed_10m"),
            wind_direction_deg=pick("wind_direction_10m"),
            humidity_percent=pick("relative_humidity_2m"),
            visibility_km=visibility_km,
        )
        expires_at = now_ts + settings.cache_ttl_weather
        self._cache[cache_key] = (snapshot, expires_at)
        return snapshot


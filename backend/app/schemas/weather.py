from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    time: datetime

    # Weather interpretation
    weather_code: int | None = Field(default=None)
    condition: str | None = Field(default=None)

    # Temperature
    temperature_c: float | None = Field(default=None)
    apparent_temperature_c: float | None = Field(default=None)

    # Precipitation
    precipitation_probability_pct: float | None = Field(default=None, ge=0, le=100)
    precipitation_mm: float | None = Field(default=None, ge=0)

    # Wind
    wind_speed_kmh: float | None = Field(default=None, ge=0)
    wind_direction_deg: float | None = Field(default=None, ge=0, le=360)

    # Other
    humidity_percent: float | None = Field(default=None, ge=0, le=100)
    visibility_km: float | None = Field(default=None, ge=0)


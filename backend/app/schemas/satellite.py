from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SatelliteStatus = Literal["ok", "stale", "unavailable"]


class SatelliteBounds(BaseModel):
    north: float
    south: float
    east: float
    west: float


class SatelliteObservation(BaseModel):
    timestamp: datetime
    observed_at: datetime
    received_at: datetime | None = None
    bounds: SatelliteBounds | None = None
    image_url: str | None = None
    tile_url_template: str | None = None
    source: str
    resolution_km: float | None = None
    layer: str | None = None


class SatelliteFrameResponse(BaseModel):
    status: SatelliteStatus
    provider: str
    source: str
    timestamp: datetime | None = None
    observed_at: datetime | None = None
    received_at: datetime | None = None
    tile_url_template: str | None = None
    tile_matrix_set: str | None = None
    tile_format: str | None = None
    tile_max_zoom: int = 6
    refresh_interval_seconds: int = Field(description="Suggested client refresh interval")
    stale_after_seconds: int = Field(description="Data older than this is considered stale")
    coverage: str = "asia_pacific"
    message: str | None = None

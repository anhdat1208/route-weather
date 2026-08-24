from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng

TrackState = Literal["NEW", "TRACKING", "LOST", "EXPIRED"]
RainCellTrackStatus = Literal["ok", "partial", "unavailable"]


class RainCellTrackRequest(BaseModel):
    geometry: list[LatLng] = Field(..., min_length=2)
    buffer_km: float | None = Field(default=None, ge=1, le=300)


class CellIntensityOut(BaseModel):
    min: float | None = None
    max: float | None = None
    mean: float | None = None


class CellBoundsOut(BaseModel):
    north: float
    south: float
    east: float
    west: float


class RainCellOut(BaseModel):
    id: str
    timestamp: str
    centroid: LatLng
    area_km2: float | None = None
    intensity: CellIntensityOut | None = None
    bounds: CellBoundsOut | None = None


class CellMotionOut(BaseModel):
    speed_kmh: float | None = None
    bearing_degrees: float | None = None
    from_point: LatLng | None = None
    to_point: LatLng | None = None
    confidence: float | None = None


class TrackedRainCellOut(BaseModel):
    id: str
    state: TrackState
    current: RainCellOut
    history: list[RainCellOut]
    motion: CellMotionOut | None = None
    distance_to_route_km: float | None = None
    missed_frames: int = 0


class RainCellTrackResponse(BaseModel):
    status: RainCellTrackStatus
    frames_used: int
    cells: list[TrackedRainCellOut]
    message: str | None = None

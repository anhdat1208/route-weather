from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng
from app.schemas.rain_cell import CellBoundsOut

NowcastStatus = Literal["ok", "partial", "unavailable"]


class NowcastPredictRequest(BaseModel):
    geometry: list[LatLng] = Field(..., min_length=2)
    buffer_km: float | None = Field(default=None, ge=1, le=300)


class NowcastModelInfo(BaseModel):
    name: str
    version: str


class PredictedCellMotion(BaseModel):
    speed_kmh: float | None = None
    bearing_degrees: float | None = None


class PredictedRainCell(BaseModel):
    cell_id: str
    forecast_minutes: int
    kind: Literal["predicted"] = "predicted"
    centroid: LatLng
    bounds: CellBoundsOut | None = None
    rain_probability: float | None = Field(default=None, ge=0, le=1)
    rain_intensity: float | None = None
    confidence: float = Field(..., ge=0, le=1)
    motion: PredictedCellMotion | None = None
    source: str = "rain_cell_track+baseline"


class NowcastPredictionResponse(BaseModel):
    generated_at: datetime
    status: NowcastStatus
    model: NowcastModelInfo
    frames_used: int
    radar_age_seconds: int | None = None
    horizons: list[int]
    predictions: list[PredictedRainCell]
    message: str | None = None

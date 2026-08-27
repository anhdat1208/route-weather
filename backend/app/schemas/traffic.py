from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng

TrafficStatus = Literal["ok", "partial", "unavailable"]
NowcastEmbedStatus = Literal["ok", "partial", "unavailable", "skipped"]
CongestionLevel = Literal["free", "slow", "moderate", "heavy", "severe"]
WeatherImpactLevel = Literal["none", "low", "moderate", "high"]
RoadType = Literal["arterial", "local", "unknown"]


class TrafficPredictRequest(BaseModel):
    geometry: list[LatLng] = Field(..., min_length=2)
    buffer_km: float | None = Field(default=None, ge=1, le=300)


class TrafficModelInfo(BaseModel):
    name: str
    version: str


class TrafficStateOut(BaseModel):
    current_speed_kmh: float | None = None
    free_flow_speed_kmh: float | None = None
    congestion_level: CongestionLevel | None = None
    relative_speed: float | None = None
    timestamp: datetime
    source: str
    stale: bool = False


class RoadSegmentOut(BaseModel):
    id: str
    geometry: list[LatLng]
    road_type: str | None = None
    name: str | None = None
    traffic: TrafficStateOut | None = None


class SpeedCongestionPair(BaseModel):
    speed_kmh: float | None = None
    congestion: CongestionLevel | None = None
    speed_delta_pct: float | None = None


class WeatherImpactInfo(BaseModel):
    speed_delta_pct: float
    level: WeatherImpactLevel
    rain_probability: float | None = Field(default=None, ge=0, le=1)
    rain_intensity: float | None = None
    reasons: list[str] = Field(default_factory=list)


class TrafficPredictionOut(BaseModel):
    road_segment_id: str
    forecast_minutes: int
    predicted_speed_kmh: float | None = None
    predicted_congestion: CongestionLevel | None = None
    confidence: float = Field(..., ge=0, le=1)
    base_prediction: SpeedCongestionPair
    weather_impact: WeatherImpactInfo
    weather_adjusted: SpeedCongestionPair
    model: TrafficModelInfo


class TrafficPredictionResponse(BaseModel):
    generated_at: datetime
    status: TrafficStatus
    model: TrafficModelInfo
    horizons: list[int]
    segments: list[RoadSegmentOut]
    predictions: list[TrafficPredictionOut]
    nowcast_status: NowcastEmbedStatus
    message: str | None = None

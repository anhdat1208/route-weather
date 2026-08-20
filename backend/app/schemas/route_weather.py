from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng, TravelMode
from app.schemas.weather import WeatherSnapshot


RiskLevel = Literal["very_low", "low", "moderate", "high", "very_high"]


class RouteWeatherRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    departure_time: datetime
    travel_mode: TravelMode

    # Labels for UI (optional to avoid extra geocode calls)
    origin_label: str | None = None
    destination_label: str | None = None

    # Reverse-geocode điểm trên lộ trình để hiện tên đường/khu vực trên timeline.
    geocode_route_points: bool | None = True


class PrecipitationRiskLabel(BaseModel):
    probability_pct: float
    label: Literal["LOW", "MODERATE-LOW", "MODERATE", "HIGH", "VERY HIGH"]


class RiskSummary(BaseModel):
    score: float = Field(..., ge=0, le=100)
    level: RiskLevel
    worst_segment_index: int | None = None
    summary: str


class RouteWeatherSegment(BaseModel):
    index: int
    coordinates: list[LatLng]

    arrival_time: datetime
    start_distance_km: float = Field(..., ge=0)
    end_distance_km: float = Field(..., ge=0)
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel

    weather: WeatherSnapshot

    # Nhãn cho UI timeline
    label: str | None = None


class RouteWeatherTimelinePoint(BaseModel):
    index: int
    arrival_time: datetime
    distance_km: float = Field(..., ge=0)
    label: str | None = None
    weather: WeatherSnapshot

    precipitation_probability_pct: float | None = None
    precipitation_label: PrecipitationRiskLabel | None = None


class RouteWeatherRecommendationAlternative(BaseModel):
    departure_time: datetime
    risk_score: float = Field(..., ge=0, le=100)
    level: RiskLevel


class RouteWeatherRecommendation(BaseModel):
    message: str
    alternatives: list[RouteWeatherRecommendationAlternative]


class RouteWeatherResponse(BaseModel):
    route: dict
    risk: RiskSummary
    segments: list[RouteWeatherSegment]
    timeline: list[RouteWeatherTimelinePoint]
    recommendation: RouteWeatherRecommendation


class RouteWeatherCompareRequest(BaseModel):
    request: RouteWeatherRequest
    offsets_minutes: list[int] = Field(default_factory=lambda: [0, 30, 60], min_length=1, le=240)


class RouteWeatherCompareAlternative(BaseModel):
    departure_time: datetime
    risk_score: float = Field(..., ge=0, le=100)
    level: RiskLevel


class RouteWeatherCompareResponse(BaseModel):
    baseline: RouteWeatherResponse
    alternatives: list[RouteWeatherCompareAlternative]



from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng, TravelMode
from app.schemas.route_weather import RiskLevel, WeatherStatus
from app.schemas.traffic import CongestionLevel, WeatherImpactLevel
from app.schemas.weather import WeatherSnapshot

IntelligenceStatus = Literal["ok", "partial", "unavailable"]
RiskBand = Literal["low", "moderate", "high", "severe"]


class RouteIntelligenceRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    departure_time: datetime
    travel_mode: TravelMode

    origin_label: str | None = None
    destination_label: str | None = None
    geocode_route_points: bool | None = True
    include_fusion: bool = True
    include_traffic: bool = True
    include_nowcast: bool = True


class RouteIntelligenceCompareRequest(BaseModel):
    request: RouteIntelligenceRequest
    offsets_minutes: list[int] = Field(default_factory=lambda: [0, 30, 60], min_length=1, max_length=12)


class SegmentWeatherIntel(BaseModel):
    rain_probability_pct: float | None = None
    rain_intensity_mm: float | None = None
    rain_status: str | None = None
    condition: str | None = None
    confidence: float = Field(..., ge=0, le=1)
    source: str
    prediction_horizon_minutes: int | None = None
    forecast: WeatherSnapshot | None = None
    nowcast_used: bool = False
    data_quality: str | None = None


class SegmentTrafficIntel(BaseModel):
    predicted_speed_kmh: float | None = None
    predicted_congestion: CongestionLevel | None = None
    current_congestion: CongestionLevel | None = None
    speed_reduction_pct: float | None = None
    confidence: float = Field(..., ge=0, le=1)
    weather_impact_level: WeatherImpactLevel | None = None
    weather_adjusted_speed_kmh: float | None = None
    source: str = "synthetic"
    stale: bool = False


class SegmentRiskIntel(BaseModel):
    weather_risk_score: float = Field(..., ge=0, le=100)
    weather_risk_level: RiskBand
    traffic_risk_score: float = Field(..., ge=0, le=100)
    traffic_risk_level: RiskBand
    travel_risk_score: float = Field(..., ge=0, le=100)
    travel_risk_level: RiskBand
    confidence: float = Field(..., ge=0, le=1)
    contributors: list[str] = Field(default_factory=list)


class RouteIntelligenceSegment(BaseModel):
    id: str
    index: int
    coordinates: list[LatLng]
    distance_m: float = Field(..., ge=0)
    travel_time_seconds: int = Field(..., ge=0)
    arrival_time: datetime
    label: str | None = None
    weather: SegmentWeatherIntel
    traffic: SegmentTrafficIntel | None = None
    risk: SegmentRiskIntel


class RouteIntelSummary(BaseModel):
    risk_level: RiskBand
    score: float = Field(..., ge=0, le=100)
    worst_segment_id: str | None = None
    worst_segment_index: int | None = None
    weather_status: WeatherStatus
    traffic_status: str | None = None
    confidence: float = Field(..., ge=0, le=1)
    eta_minutes: float = Field(..., ge=0)
    distance_km: float = Field(..., ge=0)
    weather_summary: str
    traffic_summary: str
    worst_condition: str | None = None


class RouteIntelExplainability(BaseModel):
    overall_risk_level: RiskBand
    score: float = Field(..., ge=0, le=100)
    main_contributors: list[str] = Field(default_factory=list)
    weather: list[str] = Field(default_factory=list)
    traffic: list[str] = Field(default_factory=list)
    worst_segment_id: str | None = None
    confidence: float = Field(..., ge=0, le=1)


class RouteIntelRecommendation(BaseModel):
    message: str
    details: list[str] = Field(default_factory=list)


class DepartureAlternative(BaseModel):
    departure_time: datetime
    offset_minutes: int
    risk_level: RiskBand
    score: float = Field(..., ge=0, le=100)


class RouteIntelligenceResponse(BaseModel):
    generated_at: datetime
    status: IntelligenceStatus
    route: dict
    summary: RouteIntelSummary
    segments: list[RouteIntelligenceSegment]
    recommendation: RouteIntelRecommendation
    explainability: RouteIntelExplainability
    departure_alternatives: list[DepartureAlternative] = Field(default_factory=list)


class RouteIntelligenceCompareResponse(BaseModel):
    baseline: RouteIntelligenceResponse
    alternatives: list[DepartureAlternative]


class RouteCompareItem(BaseModel):
    route_id: str
    distance_km: float
    eta_minutes: float
    weather_risk_level: RiskBand
    traffic_risk_level: RiskBand
    overall_risk_level: RiskBand
    score: float = Field(..., ge=0, le=100)
    tradeoff_note: str | None = None


class MultiRouteCompareRequest(BaseModel):
    request: RouteIntelligenceRequest
    """When alternate routes are not available from routing, only baseline is returned."""


class MultiRouteCompareResponse(BaseModel):
    routes: list[RouteCompareItem]
    recommendation: RouteIntelRecommendation

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng, TravelMode
from app.schemas.weather import WeatherSnapshot

DataQuality = Literal["GOOD", "STALE", "MISSING", "CONFLICTING", "UNKNOWN"]


class ObservationMetadata(BaseModel):
    source: str
    observed_at: datetime
    received_at: datetime | None = None
    age_seconds: int | None = None


class SourceQuality(BaseModel):
    forecast: DataQuality = "UNKNOWN"
    radar: DataQuality = "UNKNOWN"
    satellite: DataQuality = "UNKNOWN"
    rain_cell: DataQuality = "UNKNOWN"
    conflicts: list[str] = Field(default_factory=list)


class FusedRainCellSummary(BaseModel):
    count: int
    nearest_distance_km: float | None = None
    max_intensity_mean: float | None = None
    corridor_overlap: float | None = None


class SegmentNowcastFeatures(BaseModel):
    """Deterministic current-state features for a future nowcasting stage.

    These describe the present fused observations. They are not forecasts.
    """

    precip_probability_pct: float | None = None
    precip_mm: float | None = None
    rain_cell_count: int = 0
    nearest_rain_cell_km: float | None = None
    rain_cell_max_intensity: float | None = None
    rain_cell_corridor_overlap: float | None = None
    radar_age_seconds: int | None = None
    satellite_age_seconds: int | None = None
    radar_satellite_delta_seconds: int | None = None
    radar_available: bool = False
    satellite_available: bool = False
    precip_evidence: bool = False


class FusedSegmentState(BaseModel):
    segment_index: int
    arrival_time: datetime
    segment_start: LatLng
    segment_end: LatLng
    forecast: WeatherSnapshot | None = None
    forecast_meta: ObservationMetadata | None = None
    radar_meta: ObservationMetadata | None = None
    satellite_meta: ObservationMetadata | None = None
    rain_cell_meta: ObservationMetadata | None = None
    rain_cell: FusedRainCellSummary | None = None
    data_quality: SourceQuality
    features: SegmentNowcastFeatures
    confidence: float = Field(..., ge=0, le=1)


class WeatherFusionRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    departure_time: datetime
    travel_mode: TravelMode
    include_rain_cells: bool = True


class WeatherFusionResponse(BaseModel):
    observed_at: datetime
    route_distance_km: float
    route_duration_minutes: float
    segments: list[FusedSegmentState]
    source_versions: dict[str, str]

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.common import LatLng
from app.schemas.radar import RadarFrameResponse
from app.schemas.rain_cell import (
    CellBoundsOut,
    CellIntensityOut,
    RainCellOut,
    RainCellTrackResponse,
    TrackedRainCellOut,
)
from app.schemas.route_weather import (
    PrecipitationRiskLabel,
    RouteWeatherRecommendation,
    RouteWeatherResponse,
    RouteWeatherSegment,
    RouteWeatherTimelinePoint,
)
from app.schemas.satellite import SatelliteFrameResponse
from app.schemas.weather import WeatherSnapshot


def synthetic_route_weather() -> RouteWeatherResponse:
    base = datetime(2026, 8, 24, 3, 30, tzinfo=timezone.utc)
    seg1 = RouteWeatherSegment(
        index=0,
        coordinates=[LatLng(lat=10.75, lng=106.65), LatLng(lat=10.77, lng=106.68)],
        arrival_time=base,
        start_distance_km=0,
        end_distance_km=5,
        risk_score=10,
        risk_level="low",
        weather=WeatherSnapshot(
            time=base,
            precipitation_probability_pct=30,
            precipitation_mm=0.2,
            temperature_c=30,
        ),
        label="A",
    )
    seg2 = RouteWeatherSegment(
        index=1,
        coordinates=[LatLng(lat=10.77, lng=106.68), LatLng(lat=10.80, lng=106.72)],
        arrival_time=base + timedelta(minutes=10),
        start_distance_km=5,
        end_distance_km=10,
        risk_score=35,
        risk_level="moderate",
        weather=WeatherSnapshot(
            time=base + timedelta(minutes=10),
            precipitation_probability_pct=60,
            precipitation_mm=1.0,
            temperature_c=29,
        ),
        label="B",
    )
    timeline = [
        RouteWeatherTimelinePoint(
            index=0,
            arrival_time=base,
            distance_km=0,
            label="A",
            weather=seg1.weather,
            precipitation_probability_pct=30,
            precipitation_label=PrecipitationRiskLabel(probability_pct=30, label="MODERATE-LOW"),
        ),
        RouteWeatherTimelinePoint(
            index=1,
            arrival_time=base + timedelta(minutes=10),
            distance_km=10,
            label="B",
            weather=seg2.weather,
            precipitation_probability_pct=60,
            precipitation_label=PrecipitationRiskLabel(probability_pct=60, label="HIGH"),
        ),
    ]
    return RouteWeatherResponse(
        route={"distance_km": 10, "duration_minutes": 20},
        weather_status="ok",
        risk={"score": 30, "level": "moderate", "worst_segment_index": 1, "summary": "Synthetic"},
        segments=[seg1, seg2],
        timeline=timeline,
        recommendation=RouteWeatherRecommendation(message="", alternatives=[]),
    )


def synthetic_radar(ts: datetime | None = None) -> RadarFrameResponse:
    now = ts or datetime(2026, 8, 24, 3, 35, tzinfo=timezone.utc)
    return RadarFrameResponse(
        status="ok",
        timestamp=now,
        generated_at=now,
        tile_url_template="https://example/radar/{z}/{x}/{y}.png",
        refresh_interval_seconds=300,
        stale_after_seconds=900,
    )


def synthetic_satellite(ts: datetime | None = None, status: str = "ok") -> SatelliteFrameResponse:
    now = datetime(2026, 8, 24, 3, 35, tzinfo=timezone.utc)
    observed = ts or datetime(2026, 8, 24, 3, 30, tzinfo=timezone.utc)
    return SatelliteFrameResponse(
        status=status,  # type: ignore[arg-type]
        provider="nasa_gibs",
        source="nasa_gibs",
        timestamp=observed,
        observed_at=observed,
        received_at=now,
        tile_url_template="https://example/satellite/{z}/{x}/{y}.png",
        tile_matrix_set="GoogleMapsCompatible_Level6",
        tile_format="png",
        tile_max_zoom=6,
        refresh_interval_seconds=600,
        stale_after_seconds=1800,
        message=None,
    )


def synthetic_rain_cells(*, extra_cells: list[TrackedRainCellOut] | None = None) -> RainCellTrackResponse:
    cells = [
        TrackedRainCellOut(
            id="cell-1",
            state="TRACKING",
            current=RainCellOut(
                id="frame-1",
                timestamp="2026-08-24T03:35:00+00:00",
                centroid=LatLng(lat=10.76, lng=106.67),
                area_km2=8.5,
                intensity=CellIntensityOut(min=20, max=60, mean=40),
                bounds=CellBoundsOut(north=10.78, south=10.74, east=106.69, west=106.65),
            ),
            history=[],
            distance_to_route_km=3.2,
            missed_frames=0,
        )
    ]
    if extra_cells:
        cells.extend(extra_cells)
    return RainCellTrackResponse(
        status="ok",
        frames_used=4,
        cells=cells,
    )


def distant_rain_cell() -> TrackedRainCellOut:
    return TrackedRainCellOut(
        id="cell-far",
        state="TRACKING",
        current=RainCellOut(
            id="frame-far",
            timestamp="2026-08-24T03:35:00+00:00",
            centroid=LatLng(lat=21.03, lng=105.85),
            area_km2=20.0,
            intensity=CellIntensityOut(min=30, max=80, mean=55),
            bounds=CellBoundsOut(north=21.10, south=20.96, east=105.92, west=105.78),
        ),
        history=[],
        distance_to_route_km=1100.0,
        missed_frames=0,
    )

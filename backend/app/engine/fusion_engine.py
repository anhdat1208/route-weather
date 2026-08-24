from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings
from app.engine.geo_math import min_distance_to_polyline_m
from app.schemas.common import LatLng
from app.schemas.fusion import (
    DataQuality,
    FusedRainCellSummary,
    FusedSegmentState,
    ObservationMetadata,
    SegmentNowcastFeatures,
    SourceQuality,
    WeatherFusionResponse,
)
from app.schemas.radar import RadarFrameResponse
from app.schemas.rain_cell import CellBoundsOut, RainCellTrackResponse, TrackedRainCellOut
from app.schemas.route_weather import RouteWeatherResponse, RouteWeatherSegment
from app.schemas.satellite import SatelliteFrameResponse


def _age_seconds(observed_at: datetime, received_at: datetime | None = None) -> int:
    now = received_at or datetime.now(timezone.utc)
    if observed_at.tzinfo is None and now.tzinfo is not None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None and observed_at.tzinfo is not None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0, int((now - observed_at).total_seconds()))


def _freshness_quality(
    observed_at: datetime | None,
    stale_after_seconds: int,
    received_at: datetime | None = None,
) -> DataQuality:
    if observed_at is None:
        return "MISSING"
    age = _age_seconds(observed_at, received_at)
    return "STALE" if age > stale_after_seconds else "GOOD"


def _quality_score(quality: DataQuality) -> float:
    if quality == "GOOD":
        return 1.0
    if quality == "STALE":
        return 0.45
    if quality == "CONFLICTING":
        return 0.35
    if quality == "UNKNOWN":
        return 0.2
    return 0.0


def _segment_polyline(seg: RouteWeatherSegment) -> list[LatLng]:
    if len(seg.coordinates) >= 2:
        return list(seg.coordinates)
    return [seg.coordinates[0], seg.coordinates[-1]] if seg.coordinates else []


def _segment_bounds(polyline: list[LatLng]) -> CellBoundsOut | None:
    if not polyline:
        return None
    return CellBoundsOut(
        north=max(p.lat for p in polyline),
        south=min(p.lat for p in polyline),
        east=max(p.lng for p in polyline),
        west=min(p.lng for p in polyline),
    )


def _bbox_overlap_ratio(a: CellBoundsOut | None, b: CellBoundsOut | None) -> float | None:
    if a is None or b is None:
        return None
    lat_overlap = max(0.0, min(a.north, b.north) - max(a.south, b.south))
    lng_overlap = max(0.0, min(a.east, b.east) - max(a.west, b.west))
    if lat_overlap <= 0 or lng_overlap <= 0:
        return 0.0
    inter = lat_overlap * lng_overlap
    area_a = max(0.0, (a.north - a.south) * (a.east - a.west))
    area_b = max(0.0, (b.north - b.south) * (b.east - b.west))
    union = area_a + area_b - inter
    return round(inter / union, 3) if union > 0 else 0.0


def _associate_cells_to_segments(
    cells: list[TrackedRainCellOut],
    segments: list[RouteWeatherSegment],
    corridor_km: float,
) -> list[list[tuple[TrackedRainCellOut, float]]]:
    """Assign each cell to the nearest segment if within the corridor width."""
    assigned: list[list[tuple[TrackedRainCellOut, float]]] = [[] for _ in segments]
    polylines = [_segment_polyline(seg) for seg in segments]
    corridor_m = corridor_km * 1000.0

    for cell in cells:
        best_idx: int | None = None
        best_dist = float("inf")
        for idx, polyline in enumerate(polylines):
            if len(polyline) < 2:
                continue
            dist_m = min_distance_to_polyline_m(cell.current.centroid, polyline)
            if dist_m < best_dist:
                best_dist = dist_m
                best_idx = idx
        if best_idx is None or best_dist > corridor_m:
            continue
        assigned[best_idx].append((cell, best_dist / 1000.0))
    return assigned


def _build_observation_meta(
    source: str,
    observed_at: datetime | None,
    received_at: datetime | None,
) -> ObservationMetadata | None:
    if observed_at is None:
        return None
    return ObservationMetadata(
        source=source,
        observed_at=observed_at,
        received_at=received_at,
        age_seconds=_age_seconds(observed_at, received_at),
    )


def _segment_confidence(
    quality: SourceQuality,
    *,
    has_rain_cells: bool,
) -> float:
    score = 0.0
    score += 0.25 * _quality_score(quality.forecast)
    score += 0.25 * _quality_score(quality.radar)
    score += 0.20 * _quality_score(quality.satellite)
    rain_weight = 0.20 if has_rain_cells else 0.10
    score += rain_weight * _quality_score(quality.rain_cell)
    if not quality.conflicts:
        score += 0.10
    return round(min(1.0, max(0.0, score)), 3)


def _build_features(
    *,
    forecast,
    quality: SourceQuality,
    rain_summary: FusedRainCellSummary | None,
    radar_meta: ObservationMetadata | None,
    satellite_meta: ObservationMetadata | None,
) -> SegmentNowcastFeatures:
    radar_available = quality.radar in ("GOOD", "STALE", "CONFLICTING")
    satellite_available = quality.satellite in ("GOOD", "STALE", "CONFLICTING")
    rain_count = rain_summary.count if rain_summary else 0
    precip_evidence = bool(
        rain_count > 0 and quality.rain_cell in ("GOOD", "STALE", "CONFLICTING")
    )
    delta = None
    if radar_meta and satellite_meta:
        delta = abs(int((radar_meta.observed_at - satellite_meta.observed_at).total_seconds()))

    return SegmentNowcastFeatures(
        precip_probability_pct=forecast.precipitation_probability_pct if forecast else None,
        precip_mm=forecast.precipitation_mm if forecast else None,
        rain_cell_count=rain_count,
        nearest_rain_cell_km=rain_summary.nearest_distance_km if rain_summary else None,
        rain_cell_max_intensity=rain_summary.max_intensity_mean if rain_summary else None,
        rain_cell_corridor_overlap=rain_summary.corridor_overlap if rain_summary else None,
        radar_age_seconds=radar_meta.age_seconds if radar_meta else None,
        satellite_age_seconds=satellite_meta.age_seconds if satellite_meta else None,
        radar_satellite_delta_seconds=delta,
        radar_available=radar_available,
        satellite_available=satellite_available,
        precip_evidence=precip_evidence,
    )


def fuse_weather_state(
    *,
    route_weather: RouteWeatherResponse,
    radar: RadarFrameResponse | None,
    satellite: SatelliteFrameResponse | None,
    rain_cells: RainCellTrackResponse | None,
) -> WeatherFusionResponse:
    observed_at = datetime.now(timezone.utc)

    radar_quality = _freshness_quality(
        radar.timestamp if radar and radar.status != "unavailable" else None,
        settings.radar_stale_after_seconds,
        radar.generated_at if radar else None,
    )
    satellite_quality = _freshness_quality(
        satellite.observed_at if satellite and satellite.status != "unavailable" else None,
        settings.satellite_stale_after_seconds,
        satellite.received_at if satellite else None,
    )
    rain_cells_quality: DataQuality = "MISSING"
    if rain_cells is not None:
        if rain_cells.status == "unavailable":
            rain_cells_quality = "MISSING"
        elif rain_cells.status == "partial":
            rain_cells_quality = "STALE"
        else:
            rain_cells_quality = "GOOD"

    conflict = False
    if radar and satellite and radar.timestamp and satellite.observed_at:
        delta = abs(int((radar.timestamp - satellite.observed_at).total_seconds()))
        if delta > settings.fusion_alignment_max_seconds:
            conflict = True

    all_cells = rain_cells.cells if rain_cells and rain_cells.status != "unavailable" else []
    rain_meta_observed = None
    if all_cells:
        rain_meta_observed = max(datetime.fromisoformat(c.current.timestamp) for c in all_cells)

    assigned = _associate_cells_to_segments(
        all_cells,
        route_weather.segments,
        settings.fusion_corridor_km,
    )

    fused_segments: list[FusedSegmentState] = []
    for seg, seg_pairs in zip(route_weather.segments, assigned):
        start = seg.coordinates[0]
        end = seg.coordinates[-1]
        polyline = _segment_polyline(seg)
        seg_bounds = _segment_bounds(polyline)

        rain_summary = None
        if seg_pairs:
            nearest = min(dist for _, dist in seg_pairs)
            max_intensity = max(
                (
                    cell.current.intensity.mean
                    for cell, _ in seg_pairs
                    if cell.current.intensity and cell.current.intensity.mean is not None
                ),
                default=None,
            )
            overlaps = [
                _bbox_overlap_ratio(cell.current.bounds, seg_bounds)
                for cell, _ in seg_pairs
            ]
            overlap_vals = [v for v in overlaps if v is not None]
            rain_summary = FusedRainCellSummary(
                count=len(seg_pairs),
                nearest_distance_km=round(nearest, 2),
                max_intensity_mean=max_intensity,
                corridor_overlap=max(overlap_vals) if overlap_vals else None,
            )

        forecast_meta = _build_observation_meta(
            "open-meteo",
            seg.weather.time if seg.weather else None,
            observed_at,
        )
        forecast_quality = _freshness_quality(
            seg.weather.time if seg.weather else None,
            settings.forecast_stale_after_seconds,
            observed_at,
        )
        if seg.weather is None:
            forecast_quality = "MISSING"

        quality = SourceQuality(
            forecast=forecast_quality,
            radar=radar_quality if radar is not None else "MISSING",
            satellite=satellite_quality if satellite is not None else "MISSING",
            rain_cell=rain_cells_quality if rain_cells is not None else "MISSING",
            conflicts=["radar_satellite_time_mismatch"] if conflict else [],
        )
        if conflict and quality.radar == "GOOD":
            quality.radar = "CONFLICTING"
        if conflict and quality.satellite == "GOOD":
            quality.satellite = "CONFLICTING"

        radar_meta = _build_observation_meta(
            "rainviewer",
            radar.timestamp if radar else None,
            radar.generated_at if radar else None,
        )
        satellite_meta = _build_observation_meta(
            satellite.source if satellite else "nasa_gibs",
            satellite.observed_at if satellite else None,
            satellite.received_at if satellite else None,
        )
        features = _build_features(
            forecast=seg.weather,
            quality=quality,
            rain_summary=rain_summary,
            radar_meta=radar_meta,
            satellite_meta=satellite_meta,
        )
        confidence = _segment_confidence(quality, has_rain_cells=bool(seg_pairs))

        fused_segments.append(
            FusedSegmentState(
                segment_index=seg.index,
                arrival_time=seg.arrival_time,
                segment_start=start,
                segment_end=end,
                forecast=seg.weather,
                forecast_meta=forecast_meta,
                radar_meta=radar_meta,
                satellite_meta=satellite_meta,
                rain_cell_meta=_build_observation_meta("rain-cells", rain_meta_observed, observed_at),
                rain_cell=rain_summary,
                data_quality=quality,
                features=features,
                confidence=confidence,
            )
        )

    return WeatherFusionResponse(
        observed_at=observed_at,
        route_distance_km=route_weather.route["distance_km"],
        route_duration_minutes=route_weather.route["duration_minutes"],
        segments=fused_segments,
        source_versions={
            "forecast": "open-meteo",
            "radar": "rainviewer",
            "satellite": satellite.source if satellite else "nasa_gibs",
            "rain_cells": "stage3-baseline",
        },
    )

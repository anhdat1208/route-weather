from __future__ import annotations

from app.config import settings
from app.engine.geo_math import min_distance_to_polyline_m
from app.schemas.nowcasting import NowcastPredictionResponse, PredictedRainCell
from app.schemas.traffic import RoadSegmentOut, WeatherImpactInfo, WeatherImpactLevel

_INTENSITY_REASON: dict[WeatherImpactLevel, str] = {
    "low": "light_rain_nearby",
    "moderate": "moderate_rain_nearby",
    "high": "heavy_rain_nearby",
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _early_none(*, reasons: list[str]) -> WeatherImpactInfo:
    return WeatherImpactInfo(
        speed_delta_pct=0.0,
        level="none",
        rain_probability=None,
        rain_intensity=None,
        reasons=reasons,
    )


def _intensity_band(intensity: float | None) -> tuple[WeatherImpactLevel, float]:
    if intensity is None:
        return "low", -0.07
    if intensity < 40:
        return "low", -0.07
    if intensity < 90:
        return "moderate", -0.15
    return "high", -0.25


def _nearby_cells(
    cells: list[PredictedRainCell],
    segment: RoadSegmentOut,
) -> list[PredictedRainCell]:
    if len(segment.geometry) < 2:
        return []
    corridor_m = settings.traffic_rain_nearby_km * 1000.0
    out: list[PredictedRainCell] = []
    for cell in cells:
        dist_m = min_distance_to_polyline_m(cell.centroid, segment.geometry)
        if dist_m <= corridor_m:
            out.append(cell)
    return out


def _pick_max_intensity_cell(cells: list[PredictedRainCell]) -> PredictedRainCell:
    return max(cells, key=lambda c: c.rain_intensity if c.rain_intensity is not None else 0.0)


def estimate_impact(
    segment: RoadSegmentOut,
    *,
    horizon: int,
    nowcast: NowcastPredictionResponse | None,
) -> WeatherImpactInfo:
    if nowcast is None:
        return _early_none(reasons=["no_rain_prediction"])
    if nowcast.status == "unavailable":
        return _early_none(reasons=["nowcast_unavailable"])
    if not nowcast.predictions:
        return _early_none(reasons=["no_rain_prediction"])

    horizon_cells = [p for p in nowcast.predictions if p.forecast_minutes == horizon]
    nearby = _nearby_cells(horizon_cells, segment)
    if not nearby:
        return _early_none(reasons=["no_rain_nearby"])

    cell = _pick_max_intensity_cell(nearby)
    level, base_delta = _intensity_band(cell.rain_intensity)

    delta = base_delta
    if cell.rain_probability is not None:
        delta *= cell.rain_probability
    delta *= _clamp(cell.confidence, 0.0, 1.0)

    reasons: list[str] = []
    congestion = segment.traffic.congestion_level if segment.traffic else None
    if congestion in {"heavy", "severe"}:
        delta *= 0.5
        reasons.append("already_congested")
    if cell.confidence < 0.4:
        reasons.append("low_nowcast_confidence")
    reasons.append(_INTENSITY_REASON[level])

    return WeatherImpactInfo(
        speed_delta_pct=delta,
        level=level,
        rain_probability=cell.rain_probability,
        rain_intensity=cell.rain_intensity,
        reasons=reasons,
    )

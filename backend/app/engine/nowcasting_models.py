from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from app.config import settings
from app.engine.geo_math import destination_point
from app.schemas.common import LatLng
from app.schemas.nowcasting import PredictedCellMotion, PredictedRainCell
from app.schemas.rain_cell import CellBoundsOut, TrackedRainCellOut

_ELIGIBLE_STATES = frozenset({"TRACKING", "NEW"})


class NowcastingModel(Protocol):
    def predict(
        self,
        cells: Sequence[TrackedRainCellOut],
        *,
        frames_used: int,
        radar_age_seconds: int | None,
        horizons: list[int],
    ) -> list[PredictedRainCell]: ...


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _intensity_samples(cell: TrackedRainCellOut) -> list[tuple[float, float]]:
    dated: list[tuple[datetime, float]] = []
    for item in (*cell.history, cell.current):
        if item.intensity is None or item.intensity.mean is None:
            continue
        parsed = _parse_timestamp(item.timestamp)
        if parsed is None:
            continue
        dated.append((parsed, item.intensity.mean))
    if not dated:
        return []
    dated.sort(key=lambda pair: pair[0])
    origin = dated[0][0]
    return [((ts - origin).total_seconds() / 60.0, mean) for ts, mean in dated]


def _linear_slope(samples: list[tuple[float, float]]) -> float:
    n = len(samples)
    xs = [x for x, _ in samples]
    ys = [y for _, y in samples]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / denom


def _extrapolate_intensity(cell: TrackedRainCellOut, forecast_minutes: int) -> float | None:
    current_mean = cell.current.intensity.mean if cell.current.intensity is not None else None
    samples = _intensity_samples(cell)
    if len(samples) >= 2:
        base = current_mean if current_mean is not None else samples[-1][1]
        predicted = base + _linear_slope(samples) * forecast_minutes
    else:
        predicted = current_mean
    if predicted is None:
        return None
    return max(0.0, min(float(settings.nowcast_intensity_max), predicted))


def _confidence(
    cell: TrackedRainCellOut,
    *,
    forecast_minutes: int,
    frames_used: int,
    radar_age_seconds: int | None,
    missing_motion_vector: bool,
) -> float:
    motion = cell.motion
    base = 0.4
    if motion is not None and motion.confidence is not None:
        base = motion.confidence
    value = base * max(0.25, 1 - forecast_minutes / 90)
    if frames_used < settings.nowcast_min_frames_for_full_confidence:
        value *= 0.7
    if len(cell.history) < 2:
        value *= 0.75
    if missing_motion_vector:
        value *= 0.5
    if radar_age_seconds and radar_age_seconds > settings.radar_stale_after_seconds:
        value *= 0.6
    if missing_motion_vector:
        value = min(value, 0.35)
    return max(0.0, min(1.0, value))


def _copy_latlng(point: LatLng) -> LatLng:
    return LatLng(lat=point.lat, lng=point.lng)


def _copy_bounds(bounds: CellBoundsOut | None) -> CellBoundsOut | None:
    if bounds is None:
        return None
    return CellBoundsOut(north=bounds.north, south=bounds.south, east=bounds.east, west=bounds.west)


def _translate_bounds(bounds: CellBoundsOut, dlat: float, dlng: float) -> CellBoundsOut:
    return CellBoundsOut(
        north=bounds.north + dlat,
        south=bounds.south + dlat,
        east=bounds.east + dlng,
        west=bounds.west + dlng,
    )


class BaselineExtrapolationModel:
    @property
    def name(self) -> str:
        return settings.nowcast_model_name

    @property
    def version(self) -> str:
        return settings.nowcast_model_version

    def predict(
        self,
        cells: Sequence[TrackedRainCellOut],
        *,
        frames_used: int,
        radar_age_seconds: int | None,
        horizons: list[int],
    ) -> list[PredictedRainCell]:
        predictions: list[PredictedRainCell] = []
        for cell in cells:
            if cell.state not in _ELIGIBLE_STATES:
                continue
            predictions.extend(
                self._predict_cell(
                    cell,
                    frames_used=frames_used,
                    radar_age_seconds=radar_age_seconds,
                    horizons=horizons,
                )
            )
        return predictions

    def _predict_cell(
        self,
        cell: TrackedRainCellOut,
        *,
        frames_used: int,
        radar_age_seconds: int | None,
        horizons: list[int],
    ) -> list[PredictedRainCell]:
        motion = cell.motion
        speed = motion.speed_kmh if motion is not None else None
        bearing = motion.bearing_degrees if motion is not None else None
        missing_motion_vector = speed is None or bearing is None
        origin = cell.current.centroid
        origin_bounds = cell.current.bounds

        out: list[PredictedRainCell] = []
        for forecast_minutes in horizons:
            if missing_motion_vector:
                centroid = _copy_latlng(origin)
                bounds = _copy_bounds(origin_bounds)
            else:
                distance_km = float(speed) * (forecast_minutes / 60.0)
                centroid = destination_point(origin, distance_km, float(bearing))
                if origin_bounds is None:
                    bounds = None
                else:
                    bounds = _translate_bounds(
                        origin_bounds,
                        centroid.lat - origin.lat,
                        centroid.lng - origin.lng,
                    )

            intensity = _extrapolate_intensity(cell, forecast_minutes)
            probability = None
            if intensity is not None:
                probability = max(0.0, min(1.0, intensity / settings.nowcast_intensity_max))

            out.append(
                PredictedRainCell(
                    cell_id=cell.id,
                    forecast_minutes=forecast_minutes,
                    kind="predicted",
                    centroid=centroid,
                    bounds=bounds,
                    rain_probability=probability,
                    rain_intensity=intensity,
                    confidence=_confidence(
                        cell,
                        forecast_minutes=forecast_minutes,
                        frames_used=frames_used,
                        radar_age_seconds=radar_age_seconds,
                        missing_motion_vector=missing_motion_vector,
                    ),
                    motion=PredictedCellMotion(speed_kmh=speed, bearing_degrees=bearing),
                    source="rain_cell_track+baseline",
                )
            )
        return out

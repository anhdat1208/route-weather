from __future__ import annotations

import math
from dataclasses import dataclass

from app.config import settings
from app.engine.geo_math import cumulative_distances_m, find_point_at_distance_m
from app.schemas.common import LatLng


@dataclass(frozen=True)
class SamplePoint:
    index: int
    point: LatLng
    distance_m: float


def decide_sample_count(distance_km: float, interval_km: float | None = None) -> int:
    """Point count from spacing interval; always at least 2 (origin + destination)."""
    interval = settings.route_weather_sample_interval_km if interval_km is None else interval_km
    if interval <= 0:
        raise ValueError("interval_km must be > 0")
    # ceil so a 25 km route with 10 km interval yields points at ~0/10/20/25 (4),
    # not banker's-round(2.5)+1 which collapses to 3 in Python.
    raw = int(math.ceil(distance_km / interval)) + 1
    return max(2, raw)


def sample_points_by_distance(
    geometry: list[LatLng],
    *,
    min_points: int | None = None,
    max_points: int | None = None,
    interval_km: float | None = None,
) -> list[SamplePoint]:
    if len(geometry) < 2:
        raise ValueError("Route geometry must include at least origin and destination.")

    cum = cumulative_distances_m(geometry)
    total_m = cum[-1]
    distance_km = total_m / 1000.0

    min_points = settings.route_weather_min_points if min_points is None else min_points
    max_points = settings.route_weather_max_points if max_points is None else max_points

    count = decide_sample_count(distance_km, interval_km=interval_km)
    count = max(min_points, min(max_points, count))

    samples: list[SamplePoint] = []
    for i in range(count):
        frac = 0.0 if count == 1 else i / (count - 1)
        target_m = total_m * frac
        p = find_point_at_distance_m(geometry, cum, target_m)
        samples.append(SamplePoint(index=i, point=p, distance_m=target_m))

    return samples

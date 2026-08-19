from __future__ import annotations

import math

from app.schemas.common import LatLng


EARTH_RADIUS_M = 6371000.0


def haversine_distance_m(a: LatLng, b: LatLng) -> float:
    """Distance in meters between two WGS84 points."""

    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlat = lat2 - lat1
    dlng = math.radians(b.lng - a.lng)

    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def cumulative_distances_m(points: list[LatLng]) -> list[float]:
    """cumulative[i] = distance from points[0] to points[i] along the polyline."""
    if not points:
        return []
    cum: list[float] = [0.0]
    total = 0.0
    for i in range(1, len(points)):
        total += haversine_distance_m(points[i - 1], points[i])
        cum.append(total)
    return cum


def interpolate_point(a: LatLng, b: LatLng, f: float) -> LatLng:
    """Linear interpolation in lat/lng space (good enough for small segments)."""
    return LatLng(lat=a.lat + (b.lat - a.lat) * f, lng=a.lng + (b.lng - a.lng) * f)


def find_point_at_distance_m(points: list[LatLng], cum_dist_m: list[float], target_m: float) -> LatLng:
    if not points:
        raise ValueError("points empty")
    if len(points) != len(cum_dist_m):
        raise ValueError("points/cum_dist_m length mismatch")

    if target_m <= 0:
        return points[0]

    total = cum_dist_m[-1]
    if target_m >= total:
        return points[-1]

    # Find segment where cum crosses target.
    for i in range(1, len(points)):
        if cum_dist_m[i] >= target_m:
            prev_d = cum_dist_m[i - 1]
            next_d = cum_dist_m[i]
            if next_d == prev_d:
                f = 0.0
            else:
                f = (target_m - prev_d) / (next_d - prev_d)
            return interpolate_point(points[i - 1], points[i], f)

    return points[-1]


def slice_geometry_by_distance_m(
    points: list[LatLng],
    cum_dist_m: list[float],
    start_m: float,
    end_m: float,
) -> list[LatLng]:
    """Return polyline points covering [start_m, end_m] (inclusive), with interpolated endpoints."""
    if start_m > end_m:
        start_m, end_m = end_m, start_m

    total = cum_dist_m[-1] if cum_dist_m else 0.0
    if end_m < 0 or start_m > total:
        return []

    start_m = max(0.0, start_m)
    end_m = min(total, end_m)

    out: list[LatLng] = []
    out.append(find_point_at_distance_m(points, cum_dist_m, start_m))

    for i in range(1, len(points) - 1):
        d = cum_dist_m[i]
        if start_m < d < end_m:
            out.append(points[i])

    out.append(find_point_at_distance_m(points, cum_dist_m, end_m))

    # Avoid duplicates if interpolation hits existing vertices.
    dedup: list[LatLng] = []
    for p in out:
        if not dedup:
            dedup.append(p)
            continue
        last = dedup[-1]
        if abs(p.lat - last.lat) > 1e-9 or abs(p.lng - last.lng) > 1e-9:
            dedup.append(p)
    return dedup


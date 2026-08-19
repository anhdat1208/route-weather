from __future__ import annotations

from datetime import datetime, timedelta

from app.engine.eta import compute_eta
from app.engine.sampler import sample_points_by_distance
from app.schemas.common import LatLng


def test_eta_proportional_to_distance_ratios():
    # Single segment: sampling points should be evenly spaced in distance ratio.
    geometry = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.03, lng=106.0)]  # short route -> 5 points
    samples = sample_points_by_distance(geometry)
    departure = datetime(2026, 8, 19, 15, 30, 0)
    total_duration_ms = 30 * 60 * 1000  # 30 minutes

    eta = compute_eta(samples, departure_time=departure, total_duration_ms=total_duration_ms)
    assert len(eta) == len(samples)

    # With 5 points, ratio i/(4) => deltas should be 0, 7.5m, 15m, 22.5m, 30m.
    expected_offsets = [0, 7.5, 15, 22.5, 30]
    for i, p in enumerate(eta):
        expected_time = departure + timedelta(minutes=expected_offsets[i])
        assert abs((p.arrival_time - expected_time).total_seconds()) < 1.0


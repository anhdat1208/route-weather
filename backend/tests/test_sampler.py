from __future__ import annotations

from app.engine.sampler import decide_sample_count, sample_points_by_distance
from app.schemas.common import LatLng


def test_decide_sample_count_boundaries():
    assert decide_sample_count(4.9) == 5
    assert decide_sample_count(5.1) == 10
    assert decide_sample_count(15.0) == 10
    assert decide_sample_count(15.1) == 14
    assert decide_sample_count(50.0) == 14
    assert decide_sample_count(50.1) == 20


def test_sample_points_short_route_includes_endpoints():
    # ~3.3km (0.03 deg lat)
    geometry = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.03, lng=106.0)]
    samples = sample_points_by_distance(geometry)
    assert len(samples) == 5
    assert abs(samples[0].point.lat - geometry[0].lat) < 1e-9
    assert abs(samples[-1].point.lat - geometry[-1].lat) < 1e-9


def test_sample_points_medium_route_point_count():
    # ~11km (0.10 deg lat)
    geometry = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.10, lng=106.0)]
    samples = sample_points_by_distance(geometry)
    assert len(samples) == 10


def test_sample_points_long_route_point_count():
    # ~22km (0.20 deg lat)
    geometry = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.20, lng=106.0)]
    samples = sample_points_by_distance(geometry)
    assert len(samples) == 14


def test_sample_points_very_long_route_point_count():
    # ~66km (0.60 deg lat)
    geometry = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.60, lng=106.0)]
    samples = sample_points_by_distance(geometry)
    assert len(samples) == 20


from __future__ import annotations

from app.config import settings
from app.engine.sampler import decide_sample_count, sample_points_by_distance
from app.schemas.common import LatLng


def test_decide_sample_count_uses_interval():
    # 25 km / 10 km → round(2.5)+1 = 4
    assert decide_sample_count(25.0, interval_km=10.0) == 4
    # 100 km / 10 → 11
    assert decide_sample_count(100.0, interval_km=10.0) == 11
    # tiny route still returns at least 2 before clamp (endpoints)
    assert decide_sample_count(1.0, interval_km=10.0) == 2


def test_sample_points_respects_min_max(monkeypatch):
    monkeypatch.setattr(settings, "route_weather_sample_interval_km", 10.0)
    monkeypatch.setattr(settings, "route_weather_min_points", 5)
    monkeypatch.setattr(settings, "route_weather_max_points", 20)

    # ~3.3 km → raw count 2, clamped to min 5
    short = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.03, lng=106.0)]
    assert len(sample_points_by_distance(short)) == 5
    assert abs(sample_points_by_distance(short)[0].point.lat - 10.0) < 1e-9
    assert abs(sample_points_by_distance(short)[-1].point.lat - 10.03) < 1e-9

    # ~66 km → round(6.6)+1=8, within [5,20]
    long_geo = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.60, lng=106.0)]
    assert len(sample_points_by_distance(long_geo)) == 8


def test_sample_points_caps_at_max(monkeypatch):
    monkeypatch.setattr(settings, "route_weather_sample_interval_km", 1.0)
    monkeypatch.setattr(settings, "route_weather_min_points", 5)
    monkeypatch.setattr(settings, "route_weather_max_points", 20)
    # ~66 km / 1 km → 67 raw, capped at 20
    geometry = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.60, lng=106.0)]
    assert len(sample_points_by_distance(geometry)) == 20

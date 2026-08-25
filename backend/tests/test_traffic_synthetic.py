from __future__ import annotations

from datetime import datetime, timezone

from app.providers.synthetic_traffic import SyntheticTrafficProvider
from app.schemas.common import LatLng


GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]


def test_synthetic_builds_labeled_segments():
    segs = SyntheticTrafficProvider().current_for_route(
        GEOM, at=datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)  # Tue 08:00 UTC
    )
    assert len(segs) >= 1
    assert segs[0].id == "route-seg-0"
    assert segs[0].traffic is not None
    assert segs[0].traffic.source == "synthetic"
    assert segs[0].traffic.stale is False
    assert segs[0].traffic.congestion_level is not None
    assert len(segs[0].geometry) == 2


def test_synthetic_rush_hour_slower_than_night():
    p = SyntheticTrafficProvider()
    rush = p.current_for_route(GEOM, at=datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc))
    night = p.current_for_route(GEOM, at=datetime(2026, 8, 25, 2, 0, tzinfo=timezone.utc))
    assert rush[0].traffic.current_speed_kmh < night[0].traffic.current_speed_kmh


def test_synthetic_same_timestamp_is_deterministic():
    p = SyntheticTrafficProvider()
    at = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
    a = p.current_for_route(GEOM, at=at)
    b = p.current_for_route(GEOM, at=at)
    assert a[0].traffic.current_speed_kmh == b[0].traffic.current_speed_kmh

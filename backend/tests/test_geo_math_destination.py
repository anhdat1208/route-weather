from __future__ import annotations

from app.engine.geo_math import destination_point, haversine_distance_m
from app.schemas.common import LatLng


def test_destination_point_north_1km():
    origin = LatLng(lat=10.0, lng=106.0)
    dest = destination_point(origin, distance_km=1.0, bearing_degrees=0.0)
    dist_m = haversine_distance_m(origin, dest)
    assert abs(dist_m - 1000.0) < 15.0
    assert dest.lat > origin.lat
    assert abs(dest.lng - origin.lng) < 1e-4


def test_destination_point_east_and_zero():
    origin = LatLng(lat=10.0, lng=106.0)
    east = destination_point(origin, distance_km=2.0, bearing_degrees=90.0)
    assert east.lng > origin.lng
    same = destination_point(origin, distance_km=0.0, bearing_degrees=123.0)
    assert same.lat == origin.lat and same.lng == origin.lng

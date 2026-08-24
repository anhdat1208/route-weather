from __future__ import annotations

import math

from app.engine.radar_models import RadarBounds


def lat_lng_to_tile_xy(lat: float, lng: float, zoom: int) -> tuple[int, int]:
    n = 2**zoom
    x = int((lng + 180.0) / 360.0 * n)
    lat_rad = math.radians(max(min(lat, 85.05112878), -85.05112878))
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    x = max(0, min(n - 1, x))
    y = max(0, min(n - 1, y))
    return x, y


def tile_xy_bounds(zoom: int, x: int, y: int) -> RadarBounds:
    n = 2**zoom
    west = x / n * 360.0 - 180.0
    east = (x + 1) / n * 360.0 - 180.0
    north_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n)))
    south_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + 1) / n)))
    north = math.degrees(north_rad)
    south = math.degrees(south_rad)
    return RadarBounds(north=north, south=south, east=east, west=west)


def tile_range_for_bounds(bounds: RadarBounds, zoom: int) -> tuple[int, int, int, int]:
    x_min, y_north = lat_lng_to_tile_xy(bounds.north, bounds.west, zoom)
    x_max, y_south = lat_lng_to_tile_xy(bounds.south, bounds.east, zoom)
    if x_min > x_max:
        x_min, x_max = x_max, x_min
    if y_north > y_south:
        y_north, y_south = y_south, y_north
    return x_min, x_max, y_north, y_south

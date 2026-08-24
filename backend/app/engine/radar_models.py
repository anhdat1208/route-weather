from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.schemas.common import LatLng

INVALID_INTENSITY = float("nan")


@dataclass
class RadarBounds:
    north: float
    south: float
    east: float
    west: float


@dataclass
class IntensityGrid:
    """Row-major intensity grid; invalid cells use INVALID_INTENSITY."""

    width: int
    height: int
    values: list[float]
    bounds: RadarBounds

    @classmethod
    def empty(cls, width: int, height: int, bounds: RadarBounds) -> IntensityGrid:
        return cls(width=width, height=height, values=[INVALID_INTENSITY] * (width * height), bounds=bounds)

    def get(self, row: int, col: int) -> float:
        return self.values[row * self.width + col]

    def set(self, row: int, col: int, value: float) -> None:
        self.values[row * self.width + col] = value

    def pixel_to_lat_lng(self, row: int, col: int) -> LatLng:
        lng = self.bounds.west + (col + 0.5) / self.width * (self.bounds.east - self.bounds.west)
        lat = self.bounds.north - (row + 0.5) / self.height * (self.bounds.north - self.bounds.south)
        return LatLng(lat=lat, lng=lng)

    def pixel_area_km2(self, row: int, col: int) -> float:
        p = self.pixel_to_lat_lng(row, col)
        north = self.pixel_to_lat_lng(max(0, row - 1), col)
        south = self.pixel_to_lat_lng(min(self.height - 1, row + 1), col)
        west = self.pixel_to_lat_lng(row, max(0, col - 1))
        east = self.pixel_to_lat_lng(row, min(self.width - 1, col + 1))
        from app.engine.geo_math import haversine_distance_m

        lat_m = haversine_distance_m(north, south)
        lng_m = haversine_distance_m(west, east)
        return max(0.0, lat_m * lng_m) / 1_000_000.0


@dataclass
class RadarFrame:
    timestamp: datetime
    grid: IntensityGrid
    source: str = "rainviewer"

    @property
    def timestamp_iso(self) -> str:
        return self.timestamp.astimezone(timezone.utc).isoformat()


@dataclass
class CellIntensityStats:
    min: float | None = None
    max: float | None = None
    mean: float | None = None


@dataclass
class RainCellDetection:
    """Single-frame detected precipitation region."""

    frame_id: str
    timestamp: datetime
    centroid: LatLng
    area_km2: float
    area_pixels: int
    intensity: CellIntensityStats
    bounds: RadarBounds
    pixels: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class CellMotion:
    speed_kmh: float | None = None
    bearing_degrees: float | None = None
    from_point: LatLng | None = None
    to_point: LatLng | None = None
    confidence: float | None = None


TrackState = str  # NEW | TRACKING | LOST | EXPIRED


@dataclass
class TrackedRainCell:
    id: str
    state: TrackState
    current: RainCellDetection
    history: list[RainCellDetection]
    motion: CellMotion | None = None
    distance_to_route_km: float | None = None
    missed_frames: int = 0
    consecutive_hits: int = 1

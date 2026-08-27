from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.schemas.geocode import GeocodeResult
from app.schemas.common import LatLng, TravelMode
from app.schemas.traffic import RoadSegmentOut
from app.schemas.weather import WeatherSnapshot


class RouteResult:
    def __init__(self, *, geometry: list[LatLng], distance_m: float, duration_ms: int):
        self.geometry = geometry
        self.distance_m = distance_m
        self.duration_ms = duration_ms


class RouteProvider(Protocol):
    async def get_route(
        self,
        origin: LatLng,
        destination: LatLng,
        travel_mode: TravelMode,
    ) -> RouteResult:
        ...


class GeocodeProvider(Protocol):
    async def search(self, q: str, limit: int) -> list[GeocodeResult]:
        ...

    async def reverse(self, point: LatLng, radius_km: float) -> GeocodeResult | None:
        ...


class WeatherProvider(Protocol):
    async def get_forecast_at(self, *, lat: float, lng: float, time) -> WeatherSnapshot:
        ...


class RadarFrameResult:
    def __init__(
        self,
        *,
        timestamp_unix: int,
        path: str,
        host: str,
        generated_unix: int | None = None,
    ):
        self.timestamp_unix = timestamp_unix
        self.path = path
        self.host = host
        self.generated_unix = generated_unix


class RadarProvider(Protocol):
    async def fetch_current_frame(self) -> RadarFrameResult:
        ...


class TrafficProvider(Protocol):
    def current_for_route(
        self,
        geometry: list[LatLng],
        *,
        at: datetime | None = None,
    ) -> list[RoadSegmentOut]:
        ...


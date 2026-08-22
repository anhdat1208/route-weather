from __future__ import annotations

from datetime import datetime

from app.engine.route_weather_engine import RouteWeatherEngine
from app.engine.eta import compute_eta
from app.providers.base import RouteProvider, RouteResult, WeatherProvider
from app.schemas.common import LatLng, TravelMode
from app.schemas.route_weather import RouteWeatherRequest
from app.schemas.weather import WeatherSnapshot


class MockRouteProvider(RouteProvider):
    async def get_route(self, origin: LatLng, destination: LatLng, travel_mode: TravelMode) -> RouteResult:
        # Two-point straight-ish geometry.
        geometry = [origin, destination]
        # 10 minutes total travel for test determinism.
        duration_ms = 10 * 60 * 1000
        # distance_m can be any positive number; engine uses geometry distances for sampling ratios.
        distance_m = 3000.0
        return RouteResult(geometry=geometry, distance_m=distance_m, duration_ms=duration_ms)


class MockWeatherProvider(WeatherProvider):
    async def get_forecast_at(self, *, lat: float, lng: float, time: datetime) -> WeatherSnapshot:
        # Make weather depend only on the *hour* of the ETA.
        if time.hour == 16:
            return WeatherSnapshot(
                time=time,
                precipitation_probability_pct=80,
                precipitation_mm=6,
                wind_speed_kmh=20,
                visibility_km=2,
            )
        return WeatherSnapshot(
            time=time,
            precipitation_probability_pct=10,
            precipitation_mm=0,
            wind_speed_kmh=5,
            visibility_km=10,
        )


async def _compute(engine: RouteWeatherEngine, dep_time: datetime):
    req = RouteWeatherRequest(
        origin=LatLng(lat=10.0, lng=106.0),
        destination=LatLng(lat=10.03, lng=106.0),
        departure_time=dep_time,
        travel_mode="motorbike",
    )
    return await engine.compute(req)


async def test_engine_risk_changes_with_departure_time():
    engine = RouteWeatherEngine(
        route_provider=MockRouteProvider(),
        weather_provider=MockWeatherProvider(),
        geocode_provider=None,
    )

    low = await _compute(engine, datetime(2026, 8, 19, 15, 30, 0))
    high = await _compute(engine, datetime(2026, 8, 19, 16, 30, 0))

    assert low.risk.score < high.risk.score
    assert len(low.timeline) >= 5
    assert len(high.timeline) >= 5


from app.providers.errors import WeatherNotAvailableError


class FlakyWeatherProvider(WeatherProvider):
    def __init__(self, fail_indices: set[int]):
        self.fail_indices = fail_indices
        self.calls = 0

    async def get_forecast_at(self, *, lat: float, lng: float, time: datetime) -> WeatherSnapshot:
        idx = self.calls
        self.calls += 1
        if idx in self.fail_indices:
            raise WeatherNotAvailableError("simulated point failure")
        return WeatherSnapshot(
            time=time,
            precipitation_probability_pct=20,
            precipitation_mm=0,
            temperature_c=30,
            condition="Mây nhẹ",
        )


class AlwaysFailWeatherProvider(WeatherProvider):
    async def get_forecast_at(self, *, lat: float, lng: float, time: datetime) -> WeatherSnapshot:
        raise WeatherNotAvailableError("all down")


async def test_engine_partial_weather_failure_keeps_route():
    weather = FlakyWeatherProvider(fail_indices={1})
    engine = RouteWeatherEngine(
        route_provider=MockRouteProvider(),
        weather_provider=weather,
        geocode_provider=None,
    )
    result = await _compute(engine, datetime(2026, 8, 19, 15, 0, 0))
    assert result.route["distance_km"] > 0
    assert result.weather_status == "partial"
    assert any(p.weather is None for p in result.timeline)
    assert any(p.weather is not None for p in result.timeline)


async def test_engine_full_weather_failure_still_returns_route():
    engine = RouteWeatherEngine(
        route_provider=MockRouteProvider(),
        weather_provider=AlwaysFailWeatherProvider(),
        geocode_provider=None,
    )
    result = await _compute(engine, datetime(2026, 8, 19, 15, 0, 0))
    assert result.route["distance_km"] > 0
    assert result.weather_status == "unavailable"
    assert all(p.weather is None for p in result.timeline)


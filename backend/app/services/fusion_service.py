from __future__ import annotations

from app.engine.fusion_engine import fuse_weather_state
from app.engine.route_weather_engine import RouteWeatherEngine
from app.providers.graphhopper import GraphHopperRouteProvider
from app.providers.open_meteo import OpenMeteoProvider
from app.schemas.fusion import WeatherFusionRequest, WeatherFusionResponse
from app.schemas.route_weather import RouteWeatherRequest
from app.services.radar_service import get_radar_service
from app.services.rain_cell_service import get_rain_cell_service
from app.services.satellite_service import get_satellite_service


class FusionService:
    async def build_route_weather_state(self, request: WeatherFusionRequest) -> WeatherFusionResponse:
        route_request = RouteWeatherRequest(
            origin=request.origin,
            destination=request.destination,
            departure_time=request.departure_time,
            travel_mode=request.travel_mode,
            geocode_route_points=False,
        )
        route_engine = RouteWeatherEngine(
            route_provider=GraphHopperRouteProvider(),
            weather_provider=OpenMeteoProvider(),
            geocode_provider=None,
        )
        route_weather = await route_engine.compute(route_request)

        radar = await get_radar_service().get_current_radar()
        satellite = await get_satellite_service().get_latest_satellite()

        rain_cells = None
        if request.include_rain_cells:
            geometry = [p for seg in route_weather.segments for p in seg.coordinates]
            if len(geometry) >= 2:
                rain_cells = await get_rain_cell_service().track_for_route(geometry)

        return fuse_weather_state(
            route_weather=route_weather,
            radar=radar,
            satellite=satellite,
            rain_cells=rain_cells,
        )


_fusion_service: FusionService | None = None


def get_fusion_service() -> FusionService:
    global _fusion_service
    if _fusion_service is None:
        _fusion_service = FusionService()
    return _fusion_service

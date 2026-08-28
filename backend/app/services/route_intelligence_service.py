from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.engine.route_intelligence_engine import RouteIntelligenceEngine
from app.engine.route_weather_engine import RouteWeatherEngine
from app.providers.graphhopper import GraphHopperGeocodeProvider, GraphHopperRouteProvider
from app.providers.open_meteo import OpenMeteoProvider
from app.schemas.route_intelligence import (
    DepartureAlternative,
    MultiRouteCompareResponse,
    RouteCompareItem,
    RouteIntelRecommendation,
    RouteIntelligenceCompareRequest,
    RouteIntelligenceCompareResponse,
    RouteIntelligenceRequest,
    RouteIntelligenceResponse,
    MultiRouteCompareRequest,
)
from app.schemas.route_weather import RouteWeatherRequest
from app.services.fusion_service import get_fusion_service
from app.services.nowcasting_service import get_nowcasting_service
from app.services.traffic_service import get_traffic_service

logger = logging.getLogger(__name__)


def _cache_key(request: RouteIntelligenceRequest) -> str:
    payload = request.model_dump(mode="json")
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class RouteIntelligenceService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[datetime, RouteIntelligenceResponse]] = {}

    def _route_engine(self, geocode: bool) -> RouteWeatherEngine:
        geocode_provider = None
        if geocode and settings.graphhopper_api_key:
            geocode_provider = GraphHopperGeocodeProvider()
        return RouteWeatherEngine(
            route_provider=GraphHopperRouteProvider(),
            weather_provider=OpenMeteoProvider(),
            geocode_provider=geocode_provider,
        )

    def _get_cached(self, key: str) -> RouteIntelligenceResponse | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, resp = entry
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        if age > settings.intelligence_cache_ttl_seconds:
            del self._cache[key]
            return None
        return resp

    def _set_cache(self, key: str, resp: RouteIntelligenceResponse) -> None:
        self._cache[key] = (datetime.now(timezone.utc), resp)

    async def analyze(self, request: RouteIntelligenceRequest) -> RouteIntelligenceResponse:
        key = _cache_key(request)
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        geocode = request.geocode_route_points is not False
        engine = RouteIntelligenceEngine(self._route_engine(geocode))

        route_weather = await engine.route_engine.compute(
            RouteWeatherRequest(
                origin=request.origin,
                destination=request.destination,
                departure_time=request.departure_time,
                travel_mode=request.travel_mode,
                origin_label=request.origin_label,
                destination_label=request.destination_label,
                geocode_route_points=request.geocode_route_points,
            )
        )

        geometry = [p for seg in route_weather.segments for p in seg.coordinates]
        fusion = None
        traffic = None
        nowcast = None

        if request.include_fusion and len(geometry) >= 2:
            try:
                from app.schemas.fusion import WeatherFusionRequest

                fusion = await get_fusion_service().build_route_weather_state(
                    WeatherFusionRequest(
                        origin=request.origin,
                        destination=request.destination,
                        departure_time=request.departure_time,
                        travel_mode=request.travel_mode,
                        include_rain_cells=True,
                    )
                )
            except Exception:
                logger.exception("Fusion failed for route intelligence; continuing without fusion")

        if request.include_traffic and len(geometry) >= 2:
            try:
                traffic = await get_traffic_service().predict_for_route(geometry)
                nowcast_resp = await get_nowcasting_service().predict_for_route(geometry)
                nowcast = nowcast_resp
            except Exception:
                logger.exception("Traffic/nowcast failed for route intelligence")

        elif request.include_nowcast and len(geometry) >= 2:
            try:
                nowcast = await get_nowcasting_service().predict_for_route(geometry)
            except Exception:
                logger.exception("Nowcast failed for route intelligence")

        resp = await engine.analyze(
            request,
            route_weather=route_weather,
            fusion=fusion,
            traffic=traffic,
            nowcast=nowcast,
        )
        self._set_cache(key, resp)
        return resp

    async def compare_departures(
        self,
        request: RouteIntelligenceCompareRequest,
    ) -> RouteIntelligenceCompareResponse:
        offsets = sorted(set(request.offsets_minutes))
        if 0 not in offsets:
            offsets.insert(0, 0)

        alternatives: list[DepartureAlternative] = []
        baseline: RouteIntelligenceResponse | None = None

        for offset in offsets:
            payload = request.request.model_dump()
            payload["departure_time"] = request.request.departure_time + timedelta(minutes=offset)
            if offset != 0:
                payload["geocode_route_points"] = False
            alt_req = RouteIntelligenceRequest(**payload)
            try:
                resp = await self.analyze(alt_req)
            except Exception:
                logger.exception("Departure comparison failed for offset %s", offset)
                continue

            alt = DepartureAlternative(
                departure_time=alt_req.departure_time,
                offset_minutes=offset,
                risk_level=resp.summary.risk_level,
                score=resp.summary.score,
            )
            alternatives.append(alt)
            if offset == 0:
                baseline = resp

        if baseline is None:
            raise ValueError("Baseline departure analysis failed")

        baseline = baseline.model_copy(
            update={"departure_alternatives": [a for a in alternatives if a.offset_minutes != 0]}
        )
        return RouteIntelligenceCompareResponse(baseline=baseline, alternatives=alternatives)

    async def compare_routes(
        self,
        request: MultiRouteCompareRequest,
    ) -> MultiRouteCompareResponse:
        """Compare available routes. Currently only baseline route is supported."""
        baseline = await self.analyze(request.request)
        item = RouteCompareItem(
            route_id="route-a",
            distance_km=baseline.summary.distance_km,
            eta_minutes=baseline.summary.eta_minutes,
            weather_risk_level=_max_band(s.risk.weather_risk_level for s in baseline.segments),
            traffic_risk_level=_max_band(s.risk.traffic_risk_level for s in baseline.segments),
            overall_risk_level=baseline.summary.risk_level,
            score=baseline.summary.score,
            tradeoff_note=None,
        )
        return MultiRouteCompareResponse(
            routes=[item],
            recommendation=baseline.recommendation,
        )


def _max_band(levels) -> str:
    order = {"low": 0, "moderate": 1, "high": 2, "severe": 3}
    best = "low"
    for level in levels:
        if order.get(level, 0) > order.get(best, 0):
            best = level
    return best


_service: RouteIntelligenceService | None = None


def get_route_intelligence_service() -> RouteIntelligenceService:
    global _service
    if _service is None:
        _service = RouteIntelligenceService()
    return _service

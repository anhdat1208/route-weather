from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.config import settings
from app.engine.geocode_helpers import (
    build_address_label,
    build_timeline_label,
    parse_leading_house_number,
    prefer_local_hits,
    result_has_house_number,
)
from app.providers.base import GeocodeProvider, RouteProvider, RouteResult
from app.providers.errors import ProviderNotConfiguredError, ProviderRequestError
from app.schemas.common import LatLng, TravelMode
from app.schemas.geocode import GeocodeResult


class GraphHopperGeocodeProvider(GeocodeProvider):
    def __init__(
        self,
        *,
        api_key: str = settings.graphhopper_api_key,
        base_url: str = settings.graphhopper_base_url,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = http_client or httpx.AsyncClient(timeout=20.0)

    async def search(self, q: str, limit: int) -> list[GeocodeResult]:
        if not self._api_key:
            raise ProviderNotConfiguredError("GraphHopper API key is missing.")

        query = q.strip()
        if not query:
            return []

        results = self._hits_to_results(await self._fetch_hits(query, limit))
        house_number, street_query = parse_leading_house_number(query)
        if house_number and street_query:
            has_exact = any(result_has_house_number(r.label, house_number) for r in results)
            if not has_exact:
                street_hits = await self._fetch_hits(street_query, limit)
                street_hit = self._pick_best_street_hit(street_hits, street_query)
                if street_hit is not None:
                    lat, lng = self._extract_lat_lng(street_hit)
                    fallback = GeocodeResult(
                        label=query,
                        point=LatLng(lat=lat, lng=lng),
                        approximate=True,
                    )
                    results = [fallback, *results]

        return results[:limit]

    async def _fetch_hits(self, q: str, limit: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "q": q,
            "limit": limit,
            "reverse": "false",
            "key": self._api_key,
        }
        if settings.geocode_bbox:
            params["bbox"] = settings.geocode_bbox

        url = f"{self._base_url}/geocode"

        try:
            resp = await self._client.get(url, params=params)
        except httpx.HTTPError as e:
            raise ProviderRequestError(f"GraphHopper geocode request failed: {e}") from e

        if resp.status_code != 200:
            raise ProviderRequestError(
                f"GraphHopper geocode failed with {resp.status_code}: {resp.text}"
            )

        payload = resp.json()
        hits = payload.get("hits") or []
        return prefer_local_hits(hits)

    @staticmethod
    def _hits_to_results(hits: list[dict[str, Any]]) -> list[GeocodeResult]:
        results: list[GeocodeResult] = []
        for hit in hits:
            lat, lng = GraphHopperGeocodeProvider._extract_lat_lng(hit)
            label = GraphHopperGeocodeProvider._label_from_hit(hit)
            results.append(GeocodeResult(label=label, point=LatLng(lat=lat, lng=lng)))
        return results

    @staticmethod
    def _pick_best_street_hit(hits: list[dict[str, Any]], street_query: str) -> dict[str, Any] | None:
        if not hits:
            return None

        normalized_query = street_query.casefold()
        for hit in hits:
            label = build_address_label(hit).casefold()
            name = str(hit.get("name") or "").casefold()
            street = str(hit.get("street") or "").casefold()
            if normalized_query in label or normalized_query in name or normalized_query in street:
                if "hẻm" not in label and "hem" not in label:
                    return hit

        for hit in hits:
            label = build_address_label(hit).casefold()
            if "hẻm" not in label and "hem" not in label:
                return hit

        return hits[0]

    async def reverse(self, point: LatLng, radius_km: float) -> GeocodeResult | None:
        if not self._api_key:
            raise ProviderNotConfiguredError("GraphHopper API key is missing.")

        params: dict[str, Any] = {
            "reverse": "true",
            "point": f"{point.lat},{point.lng}",
            "radius": radius_km,
            "limit": 1,
            "key": self._api_key,
        }
        url = f"{self._base_url}/geocode"

        try:
            resp = await self._client.get(url, params=params)
        except httpx.HTTPError as e:
            raise ProviderRequestError(f"GraphHopper reverse geocode request failed: {e}") from e

        if resp.status_code != 200:
            raise ProviderRequestError(
                f"GraphHopper reverse geocode failed with {resp.status_code}: {resp.text}"
            )

        payload = resp.json()
        hits = payload.get("hits") or []
        if not hits:
            return None

        hit = hits[0]
        lat, lng = self._extract_lat_lng(hit)
        label = build_timeline_label(hit)
        return GeocodeResult(label=label, point=LatLng(lat=lat, lng=lng))

    @staticmethod
    def _extract_lat_lng(hit: dict[str, Any]) -> tuple[float, float]:
        # GraphHopper uses hits[i].point.lat/lng (see docs).
        point = hit.get("point") or {}
        lat = point.get("lat")
        lng = point.get("lng")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            return float(lat), float(lng)

        # Fallback: sometimes point may be nested differently.
        lat = hit.get("lat")
        lng = hit.get("lng")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            return float(lat), float(lng)

        raise ProviderRequestError("GraphHopper geocode response missing lat/lng.")

    @staticmethod
    def _label_from_hit(hit: dict[str, Any]) -> str:
        return build_address_label(hit)


class GraphHopperRouteProvider(RouteProvider):
    def __init__(
        self,
        *,
        api_key: str = settings.graphhopper_api_key,
        base_url: str = settings.graphhopper_base_url,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = http_client or httpx.AsyncClient(timeout=30.0)

    async def get_route(
        self,
        origin: LatLng,
        destination: LatLng,
        travel_mode: TravelMode,
    ) -> RouteResult:
        if not self._api_key:
            raise ProviderNotConfiguredError("GraphHopper API key is missing.")

        profile = self._profile_for_mode(travel_mode)

        params: dict[str, Any] = {
            # Directions API GET /route
            "point": [f"{origin.lat},{origin.lng}", f"{destination.lat},{destination.lng}"],
            "profile": profile,
            "calc_points": "true",
            # Important: so response contains coordinate arrays, not encoded polyline.
            "points_encoded": "false",
            "key": self._api_key,
            # Keep response smaller.
            "instructions": "false",
        }

        url = f"{self._base_url}/route"

        try:
            resp = await self._client.get(url, params=params)
        except httpx.HTTPError as e:
            raise ProviderRequestError(f"GraphHopper route request failed: {e}") from e

        if resp.status_code != 200:
            raise ProviderRequestError(f"GraphHopper route failed with {resp.status_code}: {resp.text}")

        payload = resp.json()
        paths = payload.get("paths") or []
        if not paths:
            raise ProviderRequestError("GraphHopper route response missing paths.")

        path0 = paths[0]
        distance_m = float(path0.get("distance") or 0.0)
        time_ms = int(path0.get("time") or 0)

        points_raw = path0.get("points")

        # points_encoded=false returns GeoJSON: {"type":"LineString","coordinates":[[lon,lat],...]}
        if isinstance(points_raw, dict):
            coords = points_raw.get("coordinates") or []
        elif isinstance(points_raw, list):
            coords = points_raw
        else:
            coords = []

        if not coords:
            raise ProviderRequestError("GraphHopper route response missing points.")

        geometry: list[LatLng] = []
        for p in coords:
            if (
                isinstance(p, list)
                and len(p) >= 2
                and isinstance(p[0], (int, float))
                and isinstance(p[1], (int, float))
            ):
                geometry.append(LatLng(lat=float(p[1]), lng=float(p[0])))
        if not geometry:
            raise ProviderRequestError("GraphHopper route response points could not be parsed.")

        return RouteResult(geometry=geometry, distance_m=distance_m, duration_ms=time_ms)

    def _profile_for_mode(self, travel_mode: TravelMode) -> str:
        # For free plan, GraphHopper often only allows car/bike/foot.
        if travel_mode == "walking":
            return "foot"

        return settings.graphhopper_motorbike_profile


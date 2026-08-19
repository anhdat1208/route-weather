from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.config import settings
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

        params: dict[str, Any] = {
            "q": q,
            "limit": limit,
        }
        # GraphHopper geocode uses reverse=true/false.
        params["reverse"] = "false"
        params["key"] = self._api_key

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

        results: list[GeocodeResult] = []
        for hit in hits[:limit]:
            lat, lng = self._extract_lat_lng(hit)
            label = self._label_from_hit(hit)
            results.append(GeocodeResult(label=label, point=LatLng(lat=lat, lng=lng)))
        return results

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
        label = self._label_from_hit(hit)
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
        # Prefer explicit name, then street/city.
        name = hit.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()

        # GraphHopper hits often include city/street.
        street = hit.get("street")
        city = hit.get("city")
        country = hit.get("country")
        parts = []
        for v in (street, city, country):
            if isinstance(v, str) and v.strip():
                parts.append(v.strip())
        return ", ".join(parts) if parts else "Không xác định"


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


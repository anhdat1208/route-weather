from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.config import settings
from app.engine.eta import compute_eta
from app.engine.geo_math import cumulative_distances_m, slice_geometry_by_distance_m
from app.engine.geocode_helpers import format_route_distance_label
from app.engine.risk import compute_risk_score, compute_segment_risk, overall_route_risk, precipitation_probability_label, risk_level_from_score
from app.engine.sampler import sample_points_by_distance
from app.providers.base import GeocodeProvider, RouteProvider, WeatherProvider
from app.providers.errors import ProviderNotConfiguredError
from app.schemas.common import LatLng
from app.schemas.route_weather import (
    PrecipitationRiskLabel,
    RouteWeatherCompareRequest,
    RouteWeatherRecommendation,
    RouteWeatherRecommendationAlternative,
    RouteWeatherRequest,
    RouteWeatherResponse,
    RouteWeatherSegment,
    RouteWeatherTimelinePoint,
)


def _segment_weather_label(score: float) -> str:
    level = risk_level_from_score(score)
    # Vietnamese short label for UI.
    return {
        "very_low": "Không mưa",
        "low": "Khả năng thấp",
        "moderate": "Khả năng trung bình",
        "high": "Khả năng cao",
        "very_high": "Rủi ro rất cao",
    }[level]


class RouteWeatherEngine:
    def __init__(
        self,
        *,
        route_provider: RouteProvider,
        weather_provider: WeatherProvider,
        geocode_provider: GeocodeProvider | None = None,
    ):
        self.route_provider = route_provider
        self.weather_provider = weather_provider
        self.geocode_provider = geocode_provider

    async def compute(
        self,
        request: RouteWeatherRequest,
    ) -> RouteWeatherResponse:
        route_result = await self.route_provider.get_route(
            origin=request.origin,
            destination=request.destination,
            travel_mode=request.travel_mode,
        )
        return await self._compute_from_route(request, route_result)

    async def _compute_from_route(
        self,
        request: RouteWeatherRequest,
        route_result: Any,
    ) -> RouteWeatherResponse:
        samples = sample_points_by_distance(
            route_result.geometry,
        )

        eta_points = compute_eta(
            samples,
            departure_time=request.departure_time,
            total_duration_ms=route_result.duration_ms,
        )

        total_distance_m = route_result.distance_m
        total_duration_ms = route_result.duration_ms
        cum = cumulative_distances_m(route_result.geometry)

        # 1) Query weather for each sampled point at its ETA.
        # Dedupe within one request (lat/lng might be close).
        weather_cache: dict[tuple[float, float, datetime], Any] = {}

        async def get_snapshot(idx: int, p: LatLng, t: datetime):
            key = (round(p.lat, 3), round(p.lng, 3), t.replace(minute=0, second=0, microsecond=0))
            if key in weather_cache:
                return weather_cache[key]
            snap = await self.weather_provider.get_forecast_at(lat=p.lat, lng=p.lng, time=t)
            weather_cache[key] = snap
            return snap

        weather_tasks = [get_snapshot(i, eta.sample.point, eta.arrival_time) for i, eta in enumerate(eta_points)]
        weather_snaps = await asyncio.gather(*weather_tasks)

        # 2) Optional reverse labels
        async def get_label(i: int, p: LatLng) -> str | None:
            if not self.geocode_provider:
                return None
            try:
                res = await self.geocode_provider.reverse(p, radius_km=2.0)
            except Exception:
                return None
            return res.label if res else None

        label_mode = request.geocode_route_points is not False
        labels: list[str | None] = [None] * len(samples)
        if label_mode and self.geocode_provider:
            label_tasks = [get_label(i, eta.sample.point) for i, eta in enumerate(eta_points)]
            labels = await asyncio.gather(*label_tasks)

        # 3) Risk per sample point
        sample_scores = [compute_risk_score(snap) for snap in weather_snaps]

        # 4) Build segments + overall risk.
        segments: list[RouteWeatherSegment] = []
        segment_scores: list[float] = []
        segment_durations_ms: list[int] = []

        for i in range(len(samples) - 1):
            start_eta = eta_points[i].arrival_time
            end_eta = eta_points[i + 1].arrival_time
            duration_ms = int((end_eta - start_eta).total_seconds() * 1000)

            seg = compute_segment_risk(sample_scores[i], sample_scores[i + 1])
            segment_scores.append(seg.risk_score)
            segment_durations_ms.append(duration_ms)

            start_m = samples[i].distance_m
            end_m = samples[i + 1].distance_m
            seg_coords = slice_geometry_by_distance_m(route_result.geometry, cum, start_m, end_m)

            timeline_label = labels[i]
            if i == 0 and request.origin_label:
                timeline_label = request.origin_label
            if i == len(samples) - 2 and request.destination_label:
                timeline_label = request.destination_label

            segments.append(
                RouteWeatherSegment(
                    index=i,
                    coordinates=seg_coords if seg_coords else [samples[i].point, samples[i + 1].point],
                    arrival_time=start_eta,
                    start_distance_km=samples[i].distance_m / 1000.0,
                    end_distance_km=samples[i + 1].distance_m / 1000.0,
                    risk_score=seg.risk_score,
                    risk_level=seg.risk_level,
                    weather=weather_snaps[i],
                    label=timeline_label,
                )
            )

        overall_score, overall_level, _exposure_ratio = overall_route_risk(
            segment_scores=segment_scores,
            segment_durations_ms=segment_durations_ms,
        )

        worst_idx = None
        if segment_scores:
            worst_idx = int(max(range(len(segment_scores)), key=lambda j: segment_scores[j]))

        summary = "Bạn có thể gặp mưa trên tuyến đường."
        if worst_idx is not None:
            start_label = labels[worst_idx] or (request.origin_label if worst_idx == 0 else None)
            end_label = labels[worst_idx + 1] or (
                request.destination_label if worst_idx + 1 == len(samples) - 1 else None
            )
            if start_label and end_label:
                summary = f"Đoạn nguy cơ cao nhất: {start_label} → {end_label}."
            else:
                summary = f"Đoạn nguy cơ cao nhất: Đoạn {worst_idx + 1}."

        # 5) Timeline points
        timeline: list[RouteWeatherTimelinePoint] = []
        for i, (eta, snap) in enumerate(zip(eta_points, weather_snaps)):
            label = labels[i]
            if i == 0 and request.origin_label:
                label = request.origin_label
            if i == len(eta_points) - 1 and request.destination_label:
                label = request.destination_label

            prob = snap.precipitation_probability_pct
            precip_label = (
                PrecipitationRiskLabel(
                    probability_pct=prob,
                    label=precipitation_probability_label(prob),
                )
                if prob is not None
                else None
            )

            timeline.append(
                RouteWeatherTimelinePoint(
                    index=i,
                    arrival_time=eta.arrival_time,
                    distance_km=samples[i].distance_m / 1000.0,
                    label=label or (request.origin_label if i == 0 else None) or format_route_distance_label(samples[i].distance_m / 1000.0),
                    weather=snap,
                    precipitation_probability_pct=prob,
                    precipitation_label=precip_label,
                )
            )

        # 6) Recommendation placeholder: compute in API compare endpoint for multiple departures.
        rec = RouteWeatherRecommendation(
            message="",
            alternatives=[],
        )

        # If request has compare_offsets, API handler can fill, but keep engine pure for now.
        return RouteWeatherResponse(
            route={
                "distance_km": route_result.distance_m / 1000.0,
                "duration_minutes": route_result.duration_ms / 60000.0,
            },
            risk={
                "score": overall_score,
                "level": overall_level,
                "worst_segment_index": worst_idx,
                "summary": summary,
            },
            segments=segments,
            timeline=timeline,
            recommendation=rec,
        )

    async def compute_departure_comparison(
        self,
        request: RouteWeatherRequest,
        offsets_minutes: list[int],
    ):
        # Route computed once; weather changes via ETA time.
        route_result = await self.route_provider.get_route(
            origin=request.origin,
            destination=request.destination,
            travel_mode=request.travel_mode,
        )

        from app.providers.errors import WeatherNotAvailableError

        async def compute_one(offset: int):
            payload = request.model_dump()
            payload["departure_time"] = request.departure_time + timedelta(minutes=offset)
            if offset != 0:
                payload["geocode_route_points"] = False
            alt_req = RouteWeatherRequest(**payload)
            try:
                return offset, await self._compute_from_route(alt_req, route_result)
            except WeatherNotAvailableError:
                if offset == 0:
                    raise
                return None

        raw = await asyncio.gather(*[compute_one(o) for o in offsets_minutes])
        results = [r for r in raw if r is not None]
        results.sort(key=lambda x: x[0])
        return results


from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings
from app.engine.sampler import sample_points_by_distance
from app.engine.traffic_state import (
    clamp_speed,
    congestion_from_relative,
    relative_speed,
)
from app.providers.base import TrafficProvider
from app.schemas.common import LatLng
from app.schemas.traffic import RoadSegmentOut, TrafficStateOut


def tod_factor(hour: int, weekday: int) -> float:
    """Time-of-day speed multiplier; weekday 0=Mon … 6=Sun."""
    if weekday <= 4:
        if hour in (7, 8) or hour in (17, 18):
            return 0.70
        if hour in (6, 9, 16, 19):
            return 0.82
        return 0.95
    if hour in (10, 11, 12, 17, 18):
        return 0.88
    return 0.98


class SyntheticTrafficProvider(TrafficProvider):
    def current_for_route(
        self,
        geometry: list[LatLng],
        *,
        at: datetime | None = None,
    ) -> list[RoadSegmentOut]:
        ts = at if at is not None else datetime.now(timezone.utc)
        free_flow = settings.traffic_free_flow_default_kmh

        samples = sample_points_by_distance(
            geometry,
            interval_km=settings.traffic_sample_interval_km,
            min_points=settings.traffic_sample_min_points,
            max_points=settings.traffic_sample_max_points,
        )

        factor = tod_factor(ts.hour, ts.weekday())
        segments: list[RoadSegmentOut] = []

        for i in range(len(samples) - 1):
            variation = 1.0 - 0.04 * (i % 5)
            raw = free_flow * factor * variation
            current = clamp_speed(raw, free_flow)
            rel = relative_speed(current, free_flow)

            segments.append(
                RoadSegmentOut(
                    id=f"route-seg-{i}",
                    geometry=[samples[i].point, samples[i + 1].point],
                    road_type="unknown",
                    traffic=TrafficStateOut(
                        current_speed_kmh=current,
                        free_flow_speed_kmh=free_flow,
                        congestion_level=congestion_from_relative(rel),
                        relative_speed=rel,
                        timestamp=ts,
                        source="synthetic",
                        stale=False,
                    ),
                )
            )

        return segments

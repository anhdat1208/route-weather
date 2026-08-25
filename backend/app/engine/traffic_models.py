from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol, Sequence

from app.config import settings
from app.engine.traffic_state import clamp_speed, congestion_from_relative, relative_speed
from app.engine.traffic_tod import tod_factor_at
from app.schemas.traffic import RoadSegmentOut, SpeedCongestionPair

_DRIFT = 0.40


class TrafficPredictionModel(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def predict_base(
        self,
        segments: Sequence[RoadSegmentOut],
        *,
        at: datetime,
        horizons: list[int],
    ) -> list[tuple[str, int, SpeedCongestionPair]]: ...


class BaselineTrafficModel:
    @property
    def name(self) -> str:
        return settings.traffic_model_name

    @property
    def version(self) -> str:
        return settings.traffic_model_version

    def predict_base(
        self,
        segments: Sequence[RoadSegmentOut],
        *,
        at: datetime,
        horizons: list[int],
    ) -> list[tuple[str, int, SpeedCongestionPair]]:
        out: list[tuple[str, int, SpeedCongestionPair]] = []
        for seg in segments:
            if seg.traffic is None:
                continue
            traffic = seg.traffic
            free = traffic.free_flow_speed_kmh
            if free is None:
                continue
            raw_current = traffic.current_speed_kmh
            current = free if raw_current is None else raw_current

            for h in horizons:
                at_future = at + timedelta(minutes=h)
                expected_future = clamp_speed(free * tod_factor_at(at_future), free)
                base_speed = clamp_speed(current + _DRIFT * (expected_future - current), free)
                speed_delta_pct = (base_speed / current - 1) if current > 0 else 0.0
                rel = relative_speed(base_speed, free)
                out.append(
                    (
                        seg.id,
                        h,
                        SpeedCongestionPair(
                            speed_kmh=base_speed,
                            congestion=congestion_from_relative(rel),
                            speed_delta_pct=speed_delta_pct,
                        ),
                    )
                )
        return out

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.engine.sampler import SamplePoint


@dataclass(frozen=True)
class EtaPoint:
    sample: SamplePoint
    arrival_time: datetime


def compute_eta(
    samples: list[SamplePoint],
    *,
    departure_time: datetime,
    total_duration_ms: int,
) -> list[EtaPoint]:
    if total_duration_ms <= 0:
        # Degenerate case: keep all points at departure_time
        return [EtaPoint(sample=s, arrival_time=departure_time) for s in samples]

    total_distance_m = samples[-1].distance_m if samples else 0.0
    if total_distance_m <= 0:
        return [EtaPoint(sample=s, arrival_time=departure_time) for s in samples]

    out: list[EtaPoint] = []
    for s in samples:
        ratio = s.distance_m / total_distance_m
        delta_ms = int(round(ratio * total_duration_ms))
        out.append(EtaPoint(sample=s, arrival_time=departure_time + timedelta(milliseconds=delta_ms)))
    return out


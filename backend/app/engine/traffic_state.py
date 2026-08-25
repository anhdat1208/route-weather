from __future__ import annotations

from typing import Literal

CongestionLevel = Literal["free", "slow", "moderate", "heavy", "severe"]

# relative = current / free_flow
_FREE = 0.85
_SLOW = 0.70
_MODERATE = 0.50
_HEAVY = 0.30
_MAX_VS_FREE = 1.05
_MIN_VS_FREE = 0.20


def relative_speed(current: float | None, free_flow: float | None) -> float | None:
    if current is None or free_flow is None or free_flow <= 0:
        return None
    return current / free_flow


def congestion_from_relative(relative: float | None) -> CongestionLevel | None:
    if relative is None:
        return None
    if relative >= _FREE:
        return "free"
    if relative >= _SLOW:
        return "slow"
    if relative >= _MODERATE:
        return "moderate"
    if relative >= _HEAVY:
        return "heavy"
    return "severe"


def clamp_speed(speed: float, free_flow: float | None) -> float:
    if free_flow is None or free_flow <= 0:
        return max(0.0, speed)
    return max(free_flow * _MIN_VS_FREE, min(free_flow * _MAX_VS_FREE, speed))

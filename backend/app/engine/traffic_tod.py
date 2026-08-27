from __future__ import annotations

from datetime import datetime


def hour_weekday(at: datetime) -> tuple[int, int]:
    return at.hour, at.weekday()


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


def tod_factor_at(at: datetime) -> float:
    hour, weekday = hour_weekday(at)
    return tod_factor(hour, weekday)

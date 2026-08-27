from __future__ import annotations

from app.engine.traffic_state import (
    clamp_speed,
    congestion_from_relative,
    relative_speed,
)


def test_relative_speed_and_none():
    assert relative_speed(40.0, 40.0) == 1.0
    assert abs(relative_speed(20.0, 40.0) - 0.5) < 1e-9
    assert relative_speed(None, 40.0) is None
    assert relative_speed(20.0, 0.0) is None


def test_congestion_bands():
    assert congestion_from_relative(0.95) == "free"
    assert congestion_from_relative(0.80) == "slow"
    assert congestion_from_relative(0.60) == "moderate"
    assert congestion_from_relative(0.40) == "heavy"
    assert congestion_from_relative(0.20) == "severe"
    assert congestion_from_relative(None) is None


def test_clamp_speed_band():
    assert clamp_speed(50.0, 40.0) == 42.0  # 1.05 * free_flow
    assert clamp_speed(2.0, 40.0) == 8.0    # 0.20 * free_flow floor
    assert clamp_speed(30.0, None) == 30.0

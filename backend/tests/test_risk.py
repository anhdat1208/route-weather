from __future__ import annotations

from datetime import datetime

from app.engine.risk import compute_risk_score, precipitation_probability_label, risk_level_from_score
from app.schemas.weather import WeatherSnapshot


def test_precipitation_probability_labels():
    assert precipitation_probability_label(0) == "LOW"
    assert precipitation_probability_label(20) == "LOW"
    assert precipitation_probability_label(21) == "MODERATE-LOW"
    assert precipitation_probability_label(40) == "MODERATE-LOW"
    assert precipitation_probability_label(41) == "MODERATE"
    assert precipitation_probability_label(60) == "MODERATE"
    assert precipitation_probability_label(61) == "HIGH"
    assert precipitation_probability_label(80) == "HIGH"
    assert precipitation_probability_label(81) == "VERY HIGH"


def test_risk_score_expected_value():
    # Choose values to make formula clear:
    # precip_prob=50% => 0.5 * 0.50 = 0.25
    # precip_mm=10mm => intensity=1.0 * 0.25 = 0.25
    # wind_speed=60 => factor=1.0 * 0.10 = 0.10
    # visibility_km=1 => factor=(10-1)/9 = 1.0 * 0.15 = 0.15
    # total = 0.75 => score = 75
    snap = WeatherSnapshot(
        time=datetime(2026, 8, 19, 15, 0, 0),
        precipitation_probability_pct=50,
        precipitation_mm=10,
        wind_speed_kmh=60,
        visibility_km=1,
    )
    score = compute_risk_score(snap)
    assert abs(score - 75.0) < 0.01
    assert risk_level_from_score(score) == "high"


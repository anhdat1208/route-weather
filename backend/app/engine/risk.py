from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.schemas.weather import WeatherSnapshot


def precipitation_probability_label(probability_pct: float) -> str:
    low = settings.risk_threshold_low
    moderate_low = (settings.risk_threshold_low + settings.risk_threshold_moderate) / 2  # not exact, but unused
    # Labels are based on probability thresholds, not risk score thresholds.
    # For MVP we keep them configurable via risk_threshold_* fields to avoid extra env vars.
    # We'll interpret:
    # 0-20: LOW
    # 20-40: MODERATE-LOW
    # 40-60: MODERATE
    # 60-80: HIGH
    # 80-100: VERY HIGH
    if probability_pct <= 20:
        return "LOW"
    if probability_pct <= 40:
        return "MODERATE-LOW"
    if probability_pct <= 60:
        return "MODERATE"
    if probability_pct <= 80:
        return "HIGH"
    return "VERY HIGH"


def risk_level_from_score(score: float) -> str:
    if score <= 20:
        return "very_low"
    if score <= 40:
        return "low"
    if score <= 60:
        return "moderate"
    if score <= 80:
        return "high"
    return "very_high"


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_risk_score(weather: WeatherSnapshot) -> float:
    """
    Deterministic and explainable risk score in [0,100].

    segment_risk =
        precipitationProbability × 0.50
      + precipitationIntensity   × 0.25
      + windSpeedFactor         × 0.10
      + visibilityFactor        × 0.15

    Then normalized to 0..100.
    """

    precip_prob = (weather.precipitation_probability_pct or 0.0) / 100.0

    # precipitation_mm is per hour in Open-Meteo (variable "precipitation").
    precip_mm = weather.precipitation_mm or 0.0
    precipitation_intensity = _clamp01(precip_mm / 10.0)  # 0mm ->0, >=10mm ->1

    wind_speed_kmh = weather.wind_speed_kmh or 0.0
    wind_speed_factor = _clamp01(wind_speed_kmh / 60.0)

    visibility_km = weather.visibility_km
    if visibility_km is None:
        visibility_factor = 0.0
    else:
        # >=10km ->0 risk factor, <=1km ->1 risk factor.
        visibility_factor = _clamp01((10.0 - visibility_km) / 9.0)

    score_0_to_1 = (
        precip_prob * 0.50
        + precipitation_intensity * 0.25
        + wind_speed_factor * 0.10
        + visibility_factor * 0.15
    )
    return score_0_to_1 * 100.0


@dataclass(frozen=True)
class SegmentRisk:
    risk_score: float
    risk_level: str


def compute_segment_risk(score_a: float, score_b: float) -> SegmentRisk:
    score = max(score_a, score_b)
    return SegmentRisk(risk_score=score, risk_level=risk_level_from_score(score))


def overall_route_risk(
    segment_scores: list[float],
    segment_durations_ms: list[int],
) -> tuple[float, str, float]:
    if not segment_scores:
        return 0.0, "very_low", 0.0

    max_segment = max(segment_scores)
    avg_segment = sum(segment_scores) / len(segment_scores)

    total_d = sum(segment_durations_ms) or 1
    exposed_d = 0
    for s, d in zip(segment_scores, segment_durations_ms):
        if s >= settings.risk_threshold_moderate:
            exposed_d += d
    exposure_ratio = exposed_d / total_d  # 0..1

    # overall_risk = max*0.40 + avg*0.30 + exposure_ratio*100*0.30
    overall = max_segment * 0.40 + avg_segment * 0.30 + (exposure_ratio * 100.0) * 0.30
    overall = max(0.0, min(100.0, overall))
    return overall, risk_level_from_score(overall), exposure_ratio


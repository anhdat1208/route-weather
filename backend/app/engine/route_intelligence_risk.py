"""
Route Intelligence risk scoring (Stage 7).

Methodology (application-level decision support — not scientifically validated):

Weather risk (0–100):
  Base score from Stage 1 compute_risk_score (precip prob, intensity, wind, visibility).
  Vehicle multiplier:
    - motorbike: rain/wind weighted higher (more exposed)
    - walking: rain weighted higher, wind lower
  Confidence dampening: score pulled toward neutral (40) when confidence is low.

Traffic risk (0–100):
  Derived from congestion level, relative speed, weather-adjusted speed reduction.
  Kept separate from weather risk.

Travel risk (0–100):
  travel = weather × W_weather + traffic × W_traffic (configurable weights).
  Worst-of boost: if either component >= high threshold, travel risk gets a small boost.

Route score (0–100, higher = better conditions):
  score = 100 - travel_risk (clamped).

Risk bands:
  low:      0–25
  moderate: 26–50
  high:     51–75
  severe:   76–100
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.engine.risk import compute_risk_score, risk_level_from_score
from app.schemas.common import TravelMode
from app.schemas.traffic import CongestionLevel, WeatherImpactLevel
from app.schemas.weather import WeatherSnapshot

RiskBand = str

_CONGESTION_SCORE: dict[str, float] = {
    "free": 5.0,
    "slow": 30.0,
    "moderate": 50.0,
    "heavy": 75.0,
    "severe": 95.0,
}

_IMPACT_BONUS: dict[str, float] = {
    "none": 0.0,
    "low": 5.0,
    "moderate": 15.0,
    "high": 25.0,
}


def risk_band_from_score(score: float) -> RiskBand:
    if score <= settings.intelligence_risk_band_low:
        return "low"
    if score <= settings.intelligence_risk_band_moderate:
        return "moderate"
    if score <= settings.intelligence_risk_band_high:
        return "high"
    return "severe"


def route_score_from_travel_risk(travel_risk: float) -> float:
    return max(0.0, min(100.0, 100.0 - travel_risk))


def _vehicle_weather_multiplier(mode: TravelMode) -> float:
    if mode == "motorbike":
        return settings.intelligence_vehicle_motorbike_multiplier
    if mode == "walking":
        return settings.intelligence_vehicle_walking_multiplier
    return 1.0


def _apply_confidence_dampening(score: float, confidence: float) -> float:
    neutral = settings.intelligence_confidence_neutral_score
    c = max(0.0, min(1.0, confidence))
    return score * c + neutral * (1.0 - c)


def _rain_status(prob: float | None, mm: float | None) -> str:
    p = prob or 0.0
    m = mm or 0.0
    if p >= 80 or m >= 8:
        return "heavy_rain"
    if p >= 60 or m >= 4:
        return "moderate_rain"
    if p >= 40 or m >= 1:
        return "light_rain"
    if p >= 20:
        return "possible_rain"
    return "clear"


@dataclass(frozen=True)
class WeatherRiskResult:
    score: float
    level: RiskBand
    rain_status: str
    contributors: list[str]


@dataclass(frozen=True)
class TrafficRiskResult:
    score: float
    level: RiskBand
    speed_reduction_pct: float | None
    contributors: list[str]


@dataclass(frozen=True)
class TravelRiskResult:
    score: float
    level: RiskBand
    confidence: float
    contributors: list[str]


def compute_weather_risk(
    weather: WeatherSnapshot | None,
    *,
    travel_mode: TravelMode,
    confidence: float = 1.0,
    nowcast_rain_prob: float | None = None,
) -> WeatherRiskResult:
    contributors: list[str] = []

    if weather is None:
        return WeatherRiskResult(
            score=settings.intelligence_confidence_neutral_score,
            level=risk_band_from_score(settings.intelligence_confidence_neutral_score),
            rain_status="unknown",
            contributors=["Thiếu dữ liệu thời tiết"],
        )

    base = compute_risk_score(weather)
    multiplier = _vehicle_weather_multiplier(travel_mode)
    adjusted = min(100.0, base * multiplier)

    prob = weather.precipitation_probability_pct
    mm = weather.precipitation_mm
    if nowcast_rain_prob is not None and nowcast_rain_prob > (prob or 0) / 100.0:
        nowcast_pct = nowcast_rain_prob * 100.0
        adjusted = min(100.0, max(adjusted, nowcast_pct * 0.85 * multiplier))
        contributors.append(f"Nowcast: xác suất mưa {nowcast_pct:.0f}%")

    if prob is not None and prob >= 60:
        contributors.append(f"Xác suất mưa {prob:.0f}%")
    if mm is not None and mm >= 4:
        contributors.append(f"Cường độ mưa {mm:.1f} mm/h")

    wind = weather.wind_speed_kmh
    if wind is not None and wind >= 40 and travel_mode == "motorbike":
        contributors.append(f"Gió mạnh {wind:.0f} km/h")

    dampened = _apply_confidence_dampening(adjusted, confidence)
    status = _rain_status(prob, mm)
    if nowcast_rain_prob is not None and nowcast_rain_prob >= 0.6:
        status = "heavy_rain" if nowcast_rain_prob >= 0.8 else "moderate_rain"

    return WeatherRiskResult(
        score=dampened,
        level=risk_band_from_score(dampened),
        rain_status=status,
        contributors=contributors or [f"Thời tiết: {weather.condition or status}"],
    )


def compute_traffic_risk(
    *,
    congestion: CongestionLevel | None = None,
    relative_speed: float | None = None,
    speed_reduction_pct: float | None = None,
    weather_impact_level: WeatherImpactLevel | None = None,
    confidence: float = 1.0,
    stale: bool = False,
) -> TrafficRiskResult:
    contributors: list[str] = []
    base = _CONGESTION_SCORE.get(congestion or "moderate", 40.0)

    if relative_speed is not None and relative_speed < 0.5:
        base = max(base, 60.0)
        contributors.append(f"Tốc độ tương đối thấp ({relative_speed * 100:.0f}%)")

    if speed_reduction_pct is not None and speed_reduction_pct < -0.15:
        pct = abs(speed_reduction_pct) * 100
        base = min(100.0, base + pct * 0.3)
        contributors.append(f"Giảm tốc dự kiến {pct:.0f}%")

    if weather_impact_level:
        base = min(100.0, base + _IMPACT_BONUS.get(weather_impact_level, 0.0))

    if stale:
        base *= 0.85
        contributors.append("Dữ liệu giao thông cũ")

    if congestion in {"heavy", "severe"}:
        contributors.append(f"Tắc nghẽn: {congestion}")

    dampened = _apply_confidence_dampening(base, confidence * (0.7 if stale else 1.0))
    return TrafficRiskResult(
        score=dampened,
        level=risk_band_from_score(dampened),
        speed_reduction_pct=speed_reduction_pct,
        contributors=contributors or ["Giao thông ổn định"],
    )


def compute_travel_risk(
    weather_risk: float,
    traffic_risk: float,
    *,
    weather_confidence: float,
    traffic_confidence: float,
) -> TravelRiskResult:
    w_w = settings.intelligence_weather_risk_weight
    w_t = settings.intelligence_traffic_risk_weight
    combined = weather_risk * w_w + traffic_risk * w_t

    high_threshold = settings.intelligence_risk_band_high
    if weather_risk >= high_threshold or traffic_risk >= high_threshold:
        combined = min(100.0, combined + settings.intelligence_worst_of_boost)

    confidence = min(weather_confidence, traffic_confidence)
    dampened = _apply_confidence_dampening(combined, confidence)

    contributors: list[str] = []
    if weather_risk >= settings.intelligence_risk_band_moderate:
        contributors.append(f"Rủi ro thời tiết: {risk_band_from_score(weather_risk)}")
    if traffic_risk >= settings.intelligence_risk_band_moderate:
        contributors.append(f"Rủi ro giao thông: {risk_band_from_score(traffic_risk)}")

    return TravelRiskResult(
        score=dampened,
        level=risk_band_from_score(dampened),
        confidence=confidence,
        contributors=contributors,
    )


def overall_route_risk_level(segment_travel_scores: list[float]) -> RiskBand:
    if not segment_travel_scores:
        return "low"
    worst = max(segment_travel_scores)
    return risk_band_from_score(worst)


def worst_segment_index(scores: list[float]) -> int | None:
    if not scores:
        return None
    return int(max(range(len(scores)), key=lambda i: scores[i]))

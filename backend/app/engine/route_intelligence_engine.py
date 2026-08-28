from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings
from app.engine.route_intelligence_risk import (
    compute_traffic_risk,
    compute_travel_risk,
    compute_weather_risk,
    overall_route_risk_level,
    risk_band_from_score,
    route_score_from_travel_risk,
    worst_segment_index,
)
from app.engine.route_weather_engine import RouteWeatherEngine
from app.schemas.common import LatLng, TravelMode
from app.schemas.fusion import FusedSegmentState, WeatherFusionResponse
from app.schemas.nowcasting import NowcastPredictionResponse, PredictedRainCell
from app.schemas.route_intelligence import (
    DepartureAlternative,
    RouteIntelExplainability,
    RouteIntelRecommendation,
    RouteIntelSummary,
    RouteIntelligenceRequest,
    RouteIntelligenceResponse,
    RouteIntelligenceSegment,
    SegmentRiskIntel,
    SegmentTrafficIntel,
    SegmentWeatherIntel,
)
from app.schemas.route_weather import RouteWeatherResponse, RouteWeatherSegment
from app.schemas.traffic import CongestionLevel, TrafficPredictionOut, TrafficPredictionResponse

logger = logging.getLogger(__name__)


def _segment_id(index: int) -> str:
    return f"segment-{index + 1}"


def _minutes_until(at: datetime, target: datetime) -> float:
    if at.tzinfo is None and target.tzinfo is not None:
        at = at.replace(tzinfo=timezone.utc)
    if target.tzinfo is None and at.tzinfo is not None:
        target = target.replace(tzinfo=timezone.utc)
    return (target - at).total_seconds() / 60.0


def _nearest_horizon(minutes: float, horizons: list[int]) -> int | None:
    if not horizons:
        return None
    positive = [h for h in horizons if h >= 0]
    if not positive:
        return horizons[0]
    return min(positive, key=lambda h: abs(h - max(0.0, minutes)))


def _pick_traffic_prediction(
    segment_id: str,
    minutes_from_departure: float,
    traffic: TrafficPredictionResponse | None,
) -> TrafficPredictionOut | None:
    if traffic is None or not traffic.predictions:
        return None
    seg_preds = [p for p in traffic.predictions if p.road_segment_id == segment_id]
    if not seg_preds:
        idx = segment_id.rsplit("-", 1)[-1]
        alt_id = f"route-seg-{idx}"
        seg_preds = [p for p in traffic.predictions if p.road_segment_id == alt_id]
    if not seg_preds:
        return None
    horizon = _nearest_horizon(minutes_from_departure, traffic.horizons)
    if horizon is None:
        return seg_preds[0]
    matches = [p for p in seg_preds if p.forecast_minutes == horizon]
    return matches[0] if matches else min(seg_preds, key=lambda p: abs(p.forecast_minutes - (horizon or 0)))


def _nowcast_rain_at_segment(
    segment_coords: list[LatLng],
    minutes_until_arrival: float,
    nowcast: NowcastPredictionResponse | None,
) -> float | None:
    if nowcast is None or nowcast.status == "unavailable":
        return None
    if minutes_until_arrival < 0 or minutes_until_arrival > settings.intelligence_nowcast_horizon_max_minutes:
        return None
    if not segment_coords:
        return None

    mid = segment_coords[len(segment_coords) // 2]
    best: float | None = None
    for pred in nowcast.predictions:
        if pred.forecast_minutes != _nearest_horizon(minutes_until_arrival, nowcast.horizons):
            continue
        if pred.rain_probability is None:
            continue
        dist_lat = abs(pred.centroid.lat - mid.lat)
        dist_lng = abs(pred.centroid.lng - mid.lng)
        if dist_lat > 0.3 or dist_lng > 0.3:
            continue
        if best is None or pred.rain_probability > best:
            best = pred.rain_probability
    return best


def _fused_for_segment(
    fusion: WeatherFusionResponse | None,
    index: int,
) -> FusedSegmentState | None:
    if fusion is None:
        return None
    for seg in fusion.segments:
        if seg.segment_index == index:
            return seg
    return None


def _compute_traffic_aware_durations(
    segments: list[RouteWeatherSegment],
    total_duration_ms: int,
    traffic: TrafficPredictionResponse | None,
    departure_time: datetime,
) -> list[int]:
    """Adjust segment durations using traffic predictions when available."""
    if not segments:
        return []

    base_durations: list[int] = []
    for i in range(len(segments)):
        if i + 1 < len(segments):
            delta = segments[i + 1].arrival_time - segments[i].arrival_time
        else:
            delta = timedelta(milliseconds=0)
        base_durations.append(max(0, int(delta.total_seconds() * 1000)))

    if not traffic or traffic.status == "unavailable":
        return base_durations

    adjusted: list[int] = []
    cumulative_ms = 0
    for i, seg in enumerate(segments):
        seg_id = f"route-seg-{i}"
        minutes_from_dep = _minutes_until(departure_time, seg.arrival_time)
        pred = _pick_traffic_prediction(seg_id, minutes_from_dep, traffic)
        base_ms = base_durations[i] if i < len(base_durations) else 0

        if pred is None or pred.predicted_speed_kmh is None or pred.predicted_speed_kmh <= 0:
            adjusted.append(base_ms)
            cumulative_ms += base_ms
            continue

        distance_m = max(1.0, (seg.end_distance_km - seg.start_distance_km) * 1000.0)
        traffic_ms = int((distance_m / pred.predicted_speed_kmh) * 3600 * 1000)
        blend = settings.intelligence_traffic_eta_blend
        blended = int(base_ms * (1.0 - blend) + traffic_ms * blend)
        adjusted.append(max(0, blended))
        cumulative_ms += blended

    if cumulative_ms <= 0:
        return base_durations

    scale = total_duration_ms / cumulative_ms if total_duration_ms > 0 else 1.0
    return [max(0, int(d * scale)) for d in adjusted]


def _recompute_arrival_times(
    departure_time: datetime,
    durations_ms: list[int],
) -> list[datetime]:
    times: list[datetime] = []
    cumulative = 0
    for d in durations_ms:
        times.append(departure_time + timedelta(milliseconds=cumulative))
        cumulative += d
    if times:
        times.append(departure_time + timedelta(milliseconds=cumulative))
    return times


def _weather_summary(segments: list[RouteIntelligenceSegment]) -> str:
    statuses = [s.weather.rain_status for s in segments if s.weather.rain_status]
    if any(s in {"heavy_rain", "moderate_rain"} for s in statuses):
        heavy = sum(1 for s in statuses if s == "heavy_rain")
        if heavy:
            return "Mưa lớn dự kiến trên một số đoạn"
        return "Mưa vừa dự kiến trên tuyến"
    if any(s == "light_rain" for s in statuses):
        return "Mưa nhẹ có thể xảy ra"
    return "Thời tiết thuận lợi"


def _traffic_summary(segments: list[RouteIntelligenceSegment]) -> str:
    levels = [s.traffic.predicted_congestion for s in segments if s.traffic]
    if not levels:
        return "Chưa có dữ liệu giao thông"
    if any(l in {"heavy", "severe"} for l in levels):
        return "Tắc nghẽn → nặng"
    if any(l == "moderate" for l in levels):
        return "Giao thông vừa phải → nặng"
    return "Giao thông thông thoáng"


def _build_recommendation(
    segments: list[RouteIntelligenceSegment],
    summary: RouteIntelSummary,
    alternatives: list[DepartureAlternative],
) -> RouteIntelRecommendation:
    details: list[str] = []
    worst = next((s for s in segments if s.id == summary.worst_segment_id), None)

    if worst:
        w = worst.weather.rain_status
        t = worst.traffic.predicted_congestion if worst.traffic else None
        if w in {"heavy_rain", "moderate_rain"}:
            details.append(f"Dự kiến mưa {'lớn' if w == 'heavy_rain' else 'vừa'} quanh {worst.label or worst.id}.")
        if t in {"heavy", "severe"}:
            details.append("Giao thông dự kiến tăng đáng kể gần điểm đến.")

    if summary.risk_level in {"low", "moderate"} and not details:
        return RouteIntelRecommendation(
            message="Điều kiện nhìn chung thuận lợi cho tuyến này.",
            details=details,
        )

    if worst:
        msg = f"Vấn đề lớn nhất trên tuyến là quanh {worst.label or summary.worst_segment_id}."
    else:
        msg = "Có một số rủi ro trên tuyến — xem chi tiết từng đoạn."

    if alternatives:
        best_alt = min(alternatives, key=lambda a: 100 - a.score)
        baseline = next((a for a in alternatives if a.offset_minutes == 0), None)
        if baseline and best_alt.offset_minutes != 0 and best_alt.score > baseline.score + 5:
            details.append(
                f"Xuất phát lúc {best_alt.departure_time.strftime('%H:%M')} "
                f"có thể giảm rủi ro (điểm {best_alt.score:.0f}/100)."
            )

    return RouteIntelRecommendation(message=msg, details=details)


def _build_explainability(
    segments: list[RouteIntelligenceSegment],
    summary: RouteIntelSummary,
) -> RouteIntelExplainability:
    worst = next((s for s in segments if s.id == summary.worst_segment_id), None)
    weather_lines: list[str] = []
    traffic_lines: list[str] = []

    if worst:
        w = worst.weather
        if w.rain_probability_pct is not None:
            weather_lines.append(f"Xác suất mưa: {w.rain_probability_pct:.0f}%")
        if w.rain_status:
            weather_lines.append(f"Trạng thái: {w.rain_status}")
        if worst.traffic:
            t = worst.traffic
            if t.predicted_congestion:
                traffic_lines.append(f"Tắc nghẽn: {t.predicted_congestion}")
            if t.speed_reduction_pct is not None:
                traffic_lines.append(f"Giảm tốc dự kiến: {abs(t.speed_reduction_pct) * 100:.0f}%")

    return RouteIntelExplainability(
        overall_risk_level=summary.risk_level,
        score=summary.score,
        main_contributors=(worst.risk.contributors if worst else []),
        weather=weather_lines,
        traffic=traffic_lines,
        worst_segment_id=summary.worst_segment_id,
        confidence=summary.confidence,
    )


class RouteIntelligenceEngine:
    def __init__(self, route_engine: RouteWeatherEngine):
        self.route_engine = route_engine

    async def analyze(
        self,
        request: RouteIntelligenceRequest,
        *,
        route_weather: RouteWeatherResponse | None = None,
        fusion: WeatherFusionResponse | None = None,
        traffic: TrafficPredictionResponse | None = None,
        nowcast: NowcastPredictionResponse | None = None,
        departure_alternatives: list[DepartureAlternative] | None = None,
    ) -> RouteIntelligenceResponse:
        now = datetime.now(timezone.utc)

        if route_weather is None:
            from app.schemas.route_weather import RouteWeatherRequest

            rw_req = RouteWeatherRequest(
                origin=request.origin,
                destination=request.destination,
                departure_time=request.departure_time,
                travel_mode=request.travel_mode,
                origin_label=request.origin_label,
                destination_label=request.destination_label,
                geocode_route_points=request.geocode_route_points,
            )
            route_weather = await self.route_engine.compute(rw_req)

        total_duration_ms = int(route_weather.route.get("duration_minutes", 0) * 60000)
        base_segments = route_weather.segments

        durations_ms = _compute_traffic_aware_durations(
            base_segments,
            total_duration_ms,
            traffic if request.include_traffic else None,
            request.departure_time,
        )

        arrival_times = _recompute_arrival_times(request.departure_time, durations_ms)
        intel_segments: list[RouteIntelligenceSegment] = []
        travel_scores: list[float] = []
        confidences: list[float] = []

        for i, seg in enumerate(base_segments):
            arrival = arrival_times[i] if i < len(arrival_times) else seg.arrival_time
            minutes_from_now = _minutes_until(now, arrival)
            minutes_from_dep = _minutes_until(request.departure_time, arrival)

            fused = _fused_for_segment(fusion, seg.index)
            forecast = fused.forecast if fused else seg.weather
            weather_conf = fused.confidence if fused else (0.5 if seg.weather is None else 0.85)
            if route_weather.weather_status == "partial":
                weather_conf *= 0.85
            elif route_weather.weather_status == "unavailable":
                weather_conf = 0.3

            nowcast_prob = None
            nowcast_used = False
            if request.include_nowcast and nowcast:
                nowcast_prob = _nowcast_rain_at_segment(seg.coordinates, minutes_from_now, nowcast)
                nowcast_used = nowcast_prob is not None

            weather_risk = compute_weather_risk(
                forecast,
                travel_mode=request.travel_mode,
                confidence=weather_conf,
                nowcast_rain_prob=nowcast_prob,
            )

            prob = forecast.precipitation_probability_pct if forecast else None
            if nowcast_prob is not None:
                prob = max(prob or 0, nowcast_prob * 100)

            weather_intel = SegmentWeatherIntel(
                rain_probability_pct=prob,
                rain_intensity_mm=forecast.precipitation_mm if forecast else None,
                rain_status=weather_risk.rain_status,
                condition=forecast.condition if forecast else None,
                confidence=weather_conf,
                source="nowcast+forecast" if nowcast_used else ("fusion" if fused else "forecast"),
                prediction_horizon_minutes=int(max(0, minutes_from_now)) if nowcast_used else None,
                forecast=forecast,
                nowcast_used=nowcast_used,
                data_quality=str(fused.data_quality.forecast) if fused else None,
            )

            traffic_intel: SegmentTrafficIntel | None = None
            traffic_risk_score = settings.intelligence_confidence_neutral_score
            traffic_conf = 0.3
            traffic_risk_result = compute_traffic_risk(confidence=0.3)

            if request.include_traffic and traffic:
                seg_traffic_id = f"route-seg-{i}"
                road_seg = next((s for s in traffic.segments if s.id == seg_traffic_id), None)
                pred = _pick_traffic_prediction(seg_traffic_id, minutes_from_dep, traffic)

                current_cong: CongestionLevel | None = None
                rel_speed: float | None = None
                stale = False
                if road_seg and road_seg.traffic:
                    current_cong = road_seg.traffic.congestion_level
                    rel_speed = road_seg.traffic.relative_speed
                    stale = road_seg.traffic.stale

                pred_cong = pred.predicted_congestion if pred else current_cong
                pred_speed = pred.weather_adjusted.speed_kmh if pred else None
                speed_delta = pred.weather_adjusted.speed_delta_pct if pred else None
                traffic_conf = pred.confidence if pred else (0.5 if road_seg else 0.3)

                traffic_risk_result = compute_traffic_risk(
                    congestion=pred_cong,
                    relative_speed=rel_speed,
                    speed_reduction_pct=speed_delta,
                    weather_impact_level=pred.weather_impact.level if pred else None,
                    confidence=traffic_conf,
                    stale=stale,
                )
                traffic_risk_score = traffic_risk_result.score

                traffic_intel = SegmentTrafficIntel(
                    predicted_speed_kmh=pred.predicted_speed_kmh if pred else None,
                    predicted_congestion=pred_cong,
                    current_congestion=current_cong,
                    speed_reduction_pct=speed_delta,
                    confidence=traffic_conf,
                    weather_impact_level=pred.weather_impact.level if pred else None,
                    weather_adjusted_speed_kmh=pred_speed,
                    source=road_seg.traffic.source if road_seg and road_seg.traffic else "synthetic",
                    stale=stale,
                )

            travel = compute_travel_risk(
                weather_risk.score,
                traffic_risk_score,
                weather_confidence=weather_conf,
                traffic_confidence=traffic_conf,
            )

            distance_m = max(0.0, (seg.end_distance_km - seg.start_distance_km) * 1000.0)
            travel_time_s = durations_ms[i] // 1000 if i < len(durations_ms) else 0

            risk_intel = SegmentRiskIntel(
                weather_risk_score=weather_risk.score,
                weather_risk_level=weather_risk.level,
                traffic_risk_score=traffic_risk_score,
                traffic_risk_level=traffic_risk_result.level,
                travel_risk_score=travel.score,
                travel_risk_level=travel.level,
                confidence=travel.confidence,
                contributors=weather_risk.contributors + traffic_risk_result.contributors,
            )

            intel_segments.append(
                RouteIntelligenceSegment(
                    id=_segment_id(i),
                    index=i,
                    coordinates=seg.coordinates,
                    distance_m=distance_m,
                    travel_time_seconds=travel_time_s,
                    arrival_time=arrival,
                    label=seg.label,
                    weather=weather_intel,
                    traffic=traffic_intel,
                    risk=risk_intel,
                )
            )
            travel_scores.append(travel.score)
            confidences.append(travel.confidence)

        worst_idx = worst_segment_index(travel_scores)
        worst_id = _segment_id(worst_idx) if worst_idx is not None else None
        overall_travel = max(travel_scores) if travel_scores else 0.0
        route_score = route_score_from_travel_risk(overall_travel)
        route_conf = min(confidences) if confidences else 0.5

        worst_seg = intel_segments[worst_idx] if worst_idx is not None else None
        worst_condition = None
        if worst_seg:
            w = worst_seg.weather.rain_status or "unknown"
            t = worst_seg.traffic.predicted_congestion if worst_seg.traffic else "unknown"
            worst_condition = f"{w} + {t} traffic"

        status: str = "ok"
        if route_weather.weather_status != "ok":
            status = route_weather.weather_status
        if request.include_traffic and traffic and traffic.status != "ok":
            status = "partial" if status == "ok" else status

        summary = RouteIntelSummary(
            risk_level=overall_route_risk_level(travel_scores),
            score=route_score,
            worst_segment_id=worst_id,
            worst_segment_index=worst_idx,
            weather_status=route_weather.weather_status,
            traffic_status=traffic.status if traffic else None,
            confidence=route_conf,
            eta_minutes=route_weather.route.get("duration_minutes", 0),
            distance_km=route_weather.route.get("distance_km", 0),
            weather_summary=_weather_summary(intel_segments),
            traffic_summary=_traffic_summary(intel_segments),
            worst_condition=worst_condition,
        )

        alts = departure_alternatives or []
        recommendation = _build_recommendation(intel_segments, summary, alts)
        explainability = _build_explainability(intel_segments, summary)

        return RouteIntelligenceResponse(
            generated_at=now,
            status=status,  # type: ignore[arg-type]
            route={
                "distance_km": route_weather.route.get("distance_km"),
                "duration_minutes": route_weather.route.get("duration_minutes"),
                "distance_m": int(route_weather.route.get("distance_km", 0) * 1000),
                "duration_seconds": int(route_weather.route.get("duration_minutes", 0) * 60),
            },
            summary=summary,
            segments=intel_segments,
            recommendation=recommendation,
            explainability=explainability,
            departure_alternatives=alts,
        )

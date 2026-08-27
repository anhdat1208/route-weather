from __future__ import annotations

from datetime import datetime
from typing import Sequence

from app.config import settings
from app.engine.traffic_models import BaselineTrafficModel
from app.engine.traffic_state import clamp_speed, congestion_from_relative, relative_speed
from app.engine.weather_impact import estimate_impact
from app.schemas.nowcasting import NowcastPredictionResponse
from app.schemas.traffic import (
    NowcastEmbedStatus,
    RoadSegmentOut,
    SpeedCongestionPair,
    TrafficModelInfo,
    TrafficPredictionOut,
    TrafficPredictionResponse,
    TrafficStatus,
    WeatherImpactInfo,
)

_MSG_NO_SEGMENTS = "Không có đoạn đường"
_MSG_MISSING_CURRENT = "Một số đoạn thiếu tốc độ"
_MSG_NOWCAST_UNAVAILABLE = "Thời tiết dự báo không khả dụng; dùng dự báo giao thông nền"


def _model_info() -> TrafficModelInfo:
    return TrafficModelInfo(
        name=settings.traffic_model_name,
        version=settings.traffic_model_version,
    )


def _embed_nowcast_status(nowcast: NowcastPredictionResponse | None) -> NowcastEmbedStatus:
    if nowcast is None:
        return "skipped"
    return nowcast.status  # type: ignore[return-value]


def _confidence(
    *,
    horizon: int,
    segment: RoadSegmentOut,
    impact: WeatherImpactInfo,
    nowcast_status: NowcastEmbedStatus,
) -> float:
    c = settings.traffic_base_confidence
    traffic = segment.traffic
    if traffic is not None and traffic.stale:
        c *= 0.7
    current = traffic.current_speed_kmh if traffic is not None else None
    if current is None:
        c *= 0.5
    c *= max(0.35, 1.0 - 0.012 * horizon)
    if nowcast_status not in {"ok", "skipped"} and impact.level != "none":
        c *= 0.75
    if "low_nowcast_confidence" in impact.reasons:
        c *= 0.85
    c *= 0.9  # no historical traffic in Stage 6
    return max(0.0, min(1.0, c))


def _combine(
    base_speed: float,
    impact: WeatherImpactInfo,
    *,
    free_flow: float | None,
    current: float | None,
) -> SpeedCongestionPair:
    adjusted = clamp_speed(base_speed * (1.0 + impact.speed_delta_pct), free_flow)
    adj_delta = (adjusted / current - 1.0) if current is not None and current > 0 else None
    rel = relative_speed(adjusted, free_flow)
    return SpeedCongestionPair(
        speed_kmh=adjusted,
        congestion=congestion_from_relative(rel),
        speed_delta_pct=adj_delta,
    )


def _resolve_status(
    segments: Sequence[RoadSegmentOut],
    nowcast: NowcastPredictionResponse | None,
) -> tuple[TrafficStatus, NowcastEmbedStatus, str | None]:
    if not segments:
        return "unavailable", "skipped", _MSG_NO_SEGMENTS

    nowcast_status = _embed_nowcast_status(nowcast)
    missing_current = any(
        seg.traffic is not None and seg.traffic.current_speed_kmh is None for seg in segments
    )
    if missing_current:
        return "partial", nowcast_status, _MSG_MISSING_CURRENT

    if nowcast is not None and nowcast.status == "unavailable":
        return "ok", "unavailable", _MSG_NOWCAST_UNAVAILABLE

    return "ok", nowcast_status, None


def run_traffic_prediction(
    segments: Sequence[RoadSegmentOut],
    *,
    nowcast: NowcastPredictionResponse | None,
    at: datetime,
) -> TrafficPredictionResponse:
    model = _model_info()
    horizons = settings.traffic_horizons_minutes
    status, nowcast_status, message = _resolve_status(segments, nowcast)

    if not segments:
        return TrafficPredictionResponse(
            generated_at=at,
            status=status,
            model=model,
            horizons=horizons,
            segments=[],
            predictions=[],
            nowcast_status=nowcast_status,
            message=message,
        )

    seg_by_id = {seg.id: seg for seg in segments}
    base_pairs = BaselineTrafficModel().predict_base(segments, at=at, horizons=horizons)
    predictions: list[TrafficPredictionOut] = []

    for seg_id, horizon, base_pair in base_pairs:
        segment = seg_by_id[seg_id]
        impact = estimate_impact(segment, horizon=horizon, nowcast=nowcast)
        base_speed = base_pair.speed_kmh
        if base_speed is None:
            continue
        traffic = segment.traffic
        free_flow = traffic.free_flow_speed_kmh if traffic is not None else None
        current = traffic.current_speed_kmh if traffic is not None else None
        weather_adjusted = _combine(
            base_speed,
            impact,
            free_flow=free_flow,
            current=current,
        )
        predictions.append(
            TrafficPredictionOut(
                road_segment_id=seg_id,
                forecast_minutes=horizon,
                predicted_speed_kmh=weather_adjusted.speed_kmh,
                predicted_congestion=weather_adjusted.congestion,
                confidence=_confidence(
                    horizon=horizon,
                    segment=segment,
                    impact=impact,
                    nowcast_status=nowcast_status,
                ),
                base_prediction=base_pair,
                weather_impact=impact,
                weather_adjusted=weather_adjusted,
                model=model,
            )
        )

    return TrafficPredictionResponse(
        generated_at=at,
        status=status,
        model=model,
        horizons=horizons,
        segments=list(segments),
        predictions=predictions,
        nowcast_status=nowcast_status,
        message=message,
    )

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.engine.traffic_engine import run_traffic_prediction
from app.schemas.common import LatLng
from app.schemas.nowcasting import NowcastModelInfo, NowcastPredictionResponse, PredictedRainCell
from app.schemas.traffic import (
    RoadSegmentOut,
    SpeedCongestionPair,
    TrafficStateOut,
    WeatherImpactInfo,
)

T0 = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
SEG_GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]
ON_ROUTE = LatLng(lat=10.775, lng=106.725)


def _segment(
    *,
    seg_id: str = "route-seg-0",
    current: float | None = 35.0,
    free: float = 40.0,
    stale: bool = False,
) -> RoadSegmentOut:
    rel = (current / free) if current is not None and free > 0 else None
    return RoadSegmentOut(
        id=seg_id,
        geometry=SEG_GEOM,
        traffic=TrafficStateOut(
            current_speed_kmh=current,
            free_flow_speed_kmh=free,
            congestion_level="slow" if rel and rel < 0.85 else "free",
            relative_speed=rel,
            timestamp=T0,
            source="synthetic",
            stale=stale,
        ),
    )


def _nowcast(
    *,
    status: str = "ok",
    predictions: list[PredictedRainCell] | None = None,
) -> NowcastPredictionResponse:
    return NowcastPredictionResponse(
        generated_at=T0,
        status=status,  # type: ignore[arg-type]
        model=NowcastModelInfo(name="baseline", version="0.1"),
        frames_used=3,
        horizons=[5, 10, 15, 30],
        predictions=predictions or [],
    )


def _cell(
    *,
    forecast_minutes: int = 15,
    rain_intensity: float = 120.0,
) -> PredictedRainCell:
    return PredictedRainCell(
        cell_id="c1",
        forecast_minutes=forecast_minutes,
        centroid=ON_ROUTE,
        rain_intensity=rain_intensity,
        rain_probability=1.0,
        confidence=1.0,
    )


def _mock_base(speed_kmh: float, *, horizon: int = 15) -> list[tuple[str, int, SpeedCongestionPair]]:
    return [
        (
            "route-seg-0",
            horizon,
            SpeedCongestionPair(
                speed_kmh=speed_kmh,
                congestion="slow",
                speed_delta_pct=0.0,
            ),
        )
    ]


def test_combine_base_speed_and_weather_impact():
    seg = _segment(current=35.0)
    impact = WeatherImpactInfo(
        speed_delta_pct=-0.20,
        level="moderate",
        reasons=["moderate_rain_nearby"],
    )
    with (
        patch(
            "app.engine.traffic_engine.BaselineTrafficModel.predict_base",
            return_value=_mock_base(28.0),
        ),
        patch("app.engine.traffic_engine.estimate_impact", return_value=impact),
    ):
        result = run_traffic_prediction([seg], nowcast=_nowcast(), at=T0)
    pred = result.predictions[0]
    assert pred.weather_adjusted.speed_kmh == pytest.approx(22.4)
    assert pred.predicted_speed_kmh == pytest.approx(22.4)
    assert pred.base_prediction.speed_kmh == pytest.approx(28.0)


def test_confidence_lower_at_30m_than_5m():
    seg = _segment()

    def _bases(horizons: list[int]) -> list[tuple[str, int, SpeedCongestionPair]]:
        return [
            (
                "route-seg-0",
                h,
                SpeedCongestionPair(speed_kmh=30.0, congestion="slow", speed_delta_pct=0.0),
            )
            for h in horizons
        ]

    with patch(
        "app.engine.traffic_engine.BaselineTrafficModel.predict_base",
        side_effect=lambda segments, *, at, horizons: _bases(horizons),
    ):
        result = run_traffic_prediction([seg], nowcast=_nowcast(), at=T0)
    by_horizon = {p.forecast_minutes: p.confidence for p in result.predictions}
    assert by_horizon[30] < by_horizon[5]


def test_stale_traffic_lowers_confidence():
    fresh = _segment(stale=False)
    stale = _segment(stale=True)

    with patch(
        "app.engine.traffic_engine.BaselineTrafficModel.predict_base",
        return_value=_mock_base(30.0, horizon=15),
    ):
        fresh_result = run_traffic_prediction([fresh], nowcast=_nowcast(), at=T0)
        stale_result = run_traffic_prediction([stale], nowcast=_nowcast(), at=T0)
    assert stale_result.predictions[0].confidence < fresh_result.predictions[0].confidence


def test_empty_segments_unavailable():
    result = run_traffic_prediction([], nowcast=_nowcast(), at=T0)
    assert result.status == "unavailable"
    assert result.nowcast_status == "skipped"
    assert result.predictions == []
    assert result.message == "Không có đoạn đường"


def test_nowcast_unavailable_still_returns_base_predictions():
    seg = _segment()
    with patch(
        "app.engine.traffic_engine.BaselineTrafficModel.predict_base",
        return_value=_mock_base(32.0),
    ):
        result = run_traffic_prediction([seg], nowcast=_nowcast(status="unavailable"), at=T0)
    assert result.status == "ok"
    assert result.nowcast_status == "unavailable"
    assert len(result.predictions) >= 1
    pred = result.predictions[0]
    assert pred.weather_impact.speed_delta_pct == 0.0
    assert pred.weather_impact.level == "none"
    assert (
        result.message
        == "Thời tiết dự báo không khả dụng; dùng dự báo giao thông nền"
    )


def test_heavy_rain_reduces_adjusted_vs_base():
    seg = _segment()
    result = run_traffic_prediction(
        [seg],
        nowcast=_nowcast(predictions=[_cell(forecast_minutes=15, rain_intensity=120.0)]),
        at=T0,
    )
    pred = next(p for p in result.predictions if p.forecast_minutes == 15)
    assert pred.base_prediction.speed_kmh is not None
    assert pred.predicted_speed_kmh is not None
    assert pred.predicted_speed_kmh < pred.base_prediction.speed_kmh
    assert pred.weather_impact.level == "high"


def test_missing_current_speed_partial_status():
    seg = _segment(current=None)
    with patch(
        "app.engine.traffic_engine.BaselineTrafficModel.predict_base",
        return_value=_mock_base(30.0),
    ):
        result = run_traffic_prediction([seg], nowcast=_nowcast(), at=T0)
    assert result.status == "partial"
    assert result.message == "Một số đoạn thiếu tốc độ"
    assert result.predictions[0].weather_adjusted.speed_delta_pct is None

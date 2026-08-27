from __future__ import annotations

from datetime import datetime, timezone

from app.engine.weather_impact import estimate_impact
from app.schemas.common import LatLng
from app.schemas.nowcasting import NowcastModelInfo, NowcastPredictionResponse, PredictedRainCell
from app.schemas.traffic import RoadSegmentOut, TrafficStateOut

T0 = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
SEG_GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]
ON_ROUTE = LatLng(lat=10.775, lng=106.725)
FAR_AWAY = LatLng(lat=11.50, lng=107.50)


def _segment(*, congestion: str | None = "free") -> RoadSegmentOut:
    return RoadSegmentOut(
        id="route-seg-0",
        geometry=SEG_GEOM,
        traffic=TrafficStateOut(
            current_speed_kmh=35.0,
            free_flow_speed_kmh=40.0,
            congestion_level=congestion,  # type: ignore[arg-type]
            relative_speed=0.875 if congestion else None,
            timestamp=T0,
            source="synthetic",
            stale=False,
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
    centroid: LatLng = ON_ROUTE,
    rain_intensity: float | None = 30.0,
    rain_probability: float | None = 1.0,
    confidence: float = 1.0,
    cell_id: str = "c1",
) -> PredictedRainCell:
    return PredictedRainCell(
        cell_id=cell_id,
        forecast_minutes=forecast_minutes,
        centroid=centroid,
        rain_intensity=rain_intensity,
        rain_probability=rain_probability,
        confidence=confidence,
    )


def test_no_rain_nearby():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(centroid=FAR_AWAY)]),
    )
    assert impact.speed_delta_pct == 0.0
    assert impact.level == "none"
    assert impact.reasons == ["no_rain_nearby"]


def test_no_rain_prediction_empty():
    impact = estimate_impact(_segment(), horizon=15, nowcast=_nowcast(predictions=[]))
    assert impact.speed_delta_pct == 0.0
    assert impact.level == "none"
    assert impact.reasons == ["no_rain_prediction"]


def test_nowcast_unavailable():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(status="unavailable"),
    )
    assert impact.speed_delta_pct == 0.0
    assert impact.level == "none"
    assert impact.reasons == ["nowcast_unavailable"]


def test_nowcast_none():
    impact = estimate_impact(_segment(), horizon=15, nowcast=None)
    assert impact.speed_delta_pct == 0.0
    assert impact.level == "none"
    assert impact.reasons == ["no_rain_prediction"]


def test_light_rain_nearby():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=30.0)]),
    )
    assert impact.level == "low"
    assert abs(impact.speed_delta_pct - (-0.07)) < 1e-9
    assert impact.rain_intensity == 30.0
    assert impact.rain_probability == 1.0
    assert impact.reasons == ["light_rain_nearby"]


def test_heavy_rain_nearby():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=120.0)]),
    )
    assert impact.level == "high"
    assert abs(impact.speed_delta_pct - (-0.25)) < 1e-9
    assert impact.reasons == ["heavy_rain_nearby"]


def test_moderate_rain_nearby():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=60.0)]),
    )
    assert impact.level == "moderate"
    assert abs(impact.speed_delta_pct - (-0.15)) < 1e-9
    assert impact.reasons == ["moderate_rain_nearby"]


def test_none_intensity_treated_as_light():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=None)]),
    )
    assert impact.level == "low"
    assert impact.rain_intensity is None
    assert abs(impact.speed_delta_pct - (-0.07)) < 1e-9
    assert impact.reasons == ["light_rain_nearby"]


def test_already_congested_dampens_impact():
    impact = estimate_impact(
        _segment(congestion="heavy"),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=30.0)]),
    )
    assert impact.level == "low"
    assert abs(impact.speed_delta_pct - (-0.035)) < 1e-9
    assert "already_congested" in impact.reasons
    assert "light_rain_nearby" in impact.reasons


def test_severe_congestion_dampens_impact():
    impact = estimate_impact(
        _segment(congestion="severe"),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=120.0)]),
    )
    assert abs(impact.speed_delta_pct - (-0.125)) < 1e-9
    assert "already_congested" in impact.reasons


def test_low_confidence_cell():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=30.0, confidence=0.3)]),
    )
    assert abs(impact.speed_delta_pct - (-0.021)) < 1e-9
    assert "low_nowcast_confidence" in impact.reasons
    assert "light_rain_nearby" in impact.reasons


def test_rain_probability_scales_delta():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(rain_intensity=30.0, rain_probability=0.5)]),
    )
    assert abs(impact.speed_delta_pct - (-0.035)) < 1e-9


def test_picks_max_intensity_among_nearby():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(
            predictions=[
                _cell(rain_intensity=20.0, cell_id="light"),
                _cell(rain_intensity=100.0, cell_id="heavy"),
            ]
        ),
    )
    assert impact.level == "high"
    assert impact.rain_intensity == 100.0
    assert abs(impact.speed_delta_pct - (-0.25)) < 1e-9


def test_filters_by_horizon():
    impact = estimate_impact(
        _segment(),
        horizon=15,
        nowcast=_nowcast(predictions=[_cell(forecast_minutes=30, rain_intensity=120.0)]),
    )
    assert impact.level == "none"
    assert impact.reasons == ["no_rain_nearby"]

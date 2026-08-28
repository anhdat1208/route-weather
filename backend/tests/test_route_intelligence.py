from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engine.route_intelligence_engine import (
    RouteIntelligenceEngine,
    _compute_traffic_aware_durations,
    _minutes_until,
    _nearest_horizon,
    _nowcast_rain_at_segment,
    _pick_traffic_prediction,
    _recompute_arrival_times,
    _segment_id,
)
from app.engine.route_intelligence_risk import (
    compute_traffic_risk,
    compute_travel_risk,
    compute_weather_risk,
    risk_band_from_score,
    route_score_from_travel_risk,
    worst_segment_index,
)
from app.schemas.common import LatLng
from app.schemas.nowcasting import NowcastModelInfo, NowcastPredictionResponse, PredictedRainCell
from app.schemas.rain_cell import CellBoundsOut
from app.schemas.route_intelligence import RouteIntelligenceRequest
from app.schemas.route_weather import RouteWeatherResponse, RouteWeatherSegment, RiskSummary
from app.schemas.traffic import (
    RoadSegmentOut,
    SpeedCongestionPair,
    TrafficModelInfo,
    TrafficPredictionOut,
    TrafficPredictionResponse,
    TrafficStateOut,
    WeatherImpactInfo,
)
from app.schemas.weather import WeatherSnapshot


def _weather(**kwargs) -> WeatherSnapshot:
    defaults = {
        "time": datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc),
        "precipitation_probability_pct": 10.0,
        "precipitation_mm": 0.0,
        "wind_speed_kmh": 10.0,
        "visibility_km": 10.0,
    }
    defaults.update(kwargs)
    return WeatherSnapshot(**defaults)


def _route_segment(index: int, *, prob: float = 10.0, arrival_offset_min: int = 0) -> RouteWeatherSegment:
    dep = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)
    return RouteWeatherSegment(
        index=index,
        coordinates=[LatLng(lat=10.7 + index * 0.01, lng=106.6 + index * 0.01), LatLng(lat=10.71, lng=106.61)],
        arrival_time=dep + timedelta(minutes=arrival_offset_min),
        start_distance_km=index * 10.0,
        end_distance_km=(index + 1) * 10.0,
        risk_score=20.0,
        risk_level="low",
        weather=_weather(precipitation_probability_pct=prob),
        label=f"Segment {index + 1}",
    )


def _route_weather(segments: list[RouteWeatherSegment]) -> RouteWeatherResponse:
    return RouteWeatherResponse(
        route={"distance_km": 30.0, "duration_minutes": 45.0},
        weather_status="ok",
        risk=RiskSummary(score=20, level="low", worst_segment_index=0, summary="ok"),
        segments=segments,
        timeline=[],
        recommendation={"message": "", "alternatives": []},
    )


def _traffic_response() -> TrafficPredictionResponse:
    now = datetime.now(timezone.utc)
    segments = [
        RoadSegmentOut(
            id=f"route-seg-{i}",
            geometry=[LatLng(lat=10.7, lng=106.6), LatLng(lat=10.71, lng=106.61)],
            traffic=TrafficStateOut(
                current_speed_kmh=30.0,
                free_flow_speed_kmh=40.0,
                congestion_level="moderate",
                relative_speed=0.75,
                timestamp=now,
                source="synthetic",
            ),
        )
        for i in range(3)
    ]
    predictions = []
    for i in range(3):
        for horizon in [5, 10, 15, 30]:
            predictions.append(
                TrafficPredictionOut(
                    road_segment_id=f"route-seg-{i}",
                    forecast_minutes=horizon,
                    predicted_speed_kmh=25.0,
                    predicted_congestion="heavy",
                    confidence=0.7,
                    base_prediction=SpeedCongestionPair(speed_kmh=30.0, congestion="moderate"),
                    weather_impact=WeatherImpactInfo(speed_delta_pct=-0.1, level="low", reasons=[]),
                    weather_adjusted=SpeedCongestionPair(speed_kmh=27.0, congestion="moderate", speed_delta_pct=-0.1),
                    model=TrafficModelInfo(name="baseline", version="0.1"),
                )
            )
    return TrafficPredictionResponse(
        generated_at=now,
        status="ok",
        model=TrafficModelInfo(name="baseline", version="0.1"),
        horizons=[5, 10, 15, 30],
        segments=segments,
        predictions=predictions,
        nowcast_status="ok",
    )


class MockRouteEngine:
    pass


# --- Risk tests ---


def test_weather_risk_heavy_rain_motorbike_higher_than_clear():
    clear = compute_weather_risk(_weather(), travel_mode="motorbike")
    heavy = compute_weather_risk(
        _weather(precipitation_probability_pct=85, precipitation_mm=10),
        travel_mode="motorbike",
    )
    assert heavy.score > clear.score
    assert heavy.rain_status == "heavy_rain"


def test_weather_risk_low_confidence_dampened():
    high_conf = compute_weather_risk(_weather(precipitation_probability_pct=80), confidence=1.0, travel_mode="motorbike")
    low_conf = compute_weather_risk(_weather(precipitation_probability_pct=80), confidence=0.2, travel_mode="motorbike")
    assert low_conf.score < high_conf.score


def test_traffic_risk_heavy_congestion():
    free = compute_traffic_risk(congestion="free", confidence=1.0)
    heavy = compute_traffic_risk(congestion="heavy", confidence=1.0, speed_reduction_pct=-0.3)
    assert heavy.score > free.score


def test_travel_risk_combined():
    travel = compute_travel_risk(70.0, 60.0, weather_confidence=0.9, traffic_confidence=0.8)
    assert 50 < travel.score < 80
    assert travel.confidence == 0.8


def test_route_score_inverse_of_risk():
    assert route_score_from_travel_risk(30.0) == 70.0
    assert route_score_from_travel_risk(100.0) == 0.0


def test_risk_bands():
    assert risk_band_from_score(10) == "low"
    assert risk_band_from_score(40) == "moderate"
    assert risk_band_from_score(60) == "high"
    assert risk_band_from_score(90) == "severe"


def test_worst_segment_detection():
    assert worst_segment_index([10, 30, 20]) == 1


# --- Engine helper tests ---


def test_segment_id_format():
    assert _segment_id(0) == "segment-1"
    assert _segment_id(6) == "segment-7"


def test_nearest_horizon():
    assert _nearest_horizon(12, [5, 10, 15, 30]) == 10
    assert _nearest_horizon(28, [5, 10, 15, 30]) == 30


def test_pick_traffic_prediction():
    traffic = _traffic_response()
    pred = _pick_traffic_prediction("route-seg-1", 12.0, traffic)
    assert pred is not None
    assert pred.forecast_minutes == 10


def test_recompute_arrival_times():
    dep = datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc)
    times = _recompute_arrival_times(dep, [720_000, 780_000, 600_000])
    assert times[0] == dep
    assert times[1] == dep + timedelta(minutes=12)
    assert times[2] == dep + timedelta(minutes=25)


def test_traffic_aware_durations_blend():
    segs = [_route_segment(i, arrival_offset_min=i * 12) for i in range(3)]
    durations = _compute_traffic_aware_durations(segs, 45 * 60 * 1000, _traffic_response(), segs[0].arrival_time)
    assert len(durations) == 3
    assert sum(durations) > 0


def test_nowcast_rain_at_segment_within_horizon():
    nowcast = NowcastPredictionResponse(
        generated_at=datetime.now(timezone.utc),
        status="ok",
        model=NowcastModelInfo(name="baseline", version="0.1"),
        frames_used=4,
        horizons=[5, 10, 15, 30],
        predictions=[
            PredictedRainCell(
                cell_id="c1",
                forecast_minutes=10,
                centroid=LatLng(lat=10.705, lng=106.605),
                bounds=CellBoundsOut(north=10.71, south=10.70, east=106.61, west=106.60),
                rain_probability=0.82,
                confidence=0.7,
            )
        ],
    )
    coords = [LatLng(lat=10.704, lng=106.604), LatLng(lat=10.706, lng=106.606)]
    prob = _nowcast_rain_at_segment(coords, 10.0, nowcast)
    assert prob == pytest.approx(0.82)


def test_nowcast_outside_horizon_returns_none():
    nowcast = NowcastPredictionResponse(
        generated_at=datetime.now(timezone.utc),
        status="ok",
        model=NowcastModelInfo(name="baseline", version="0.1"),
        frames_used=4,
        horizons=[5, 10],
        predictions=[],
    )
    assert _nowcast_rain_at_segment([LatLng(lat=10.7, lng=106.6)], 90.0, nowcast) is None


# --- Integration-style engine test ---


@pytest.mark.asyncio
async def test_engine_analyze_clear_weather_free_traffic():
    engine = RouteIntelligenceEngine(MockRouteEngine())  # type: ignore[arg-type]
    segs = [_route_segment(i, prob=5.0) for i in range(3)]
    for i, s in enumerate(segs):
        s.arrival_time = datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc) + timedelta(minutes=i * 12)

    request = RouteIntelligenceRequest(
        origin=LatLng(lat=10.7, lng=106.6),
        destination=LatLng(lat=10.9, lng=106.8),
        departure_time=datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc),
        travel_mode="motorbike",
    )

    traffic = _traffic_response()
    for seg in traffic.segments:
        if seg.traffic:
            seg.traffic.congestion_level = "free"
            seg.traffic.current_speed_kmh = 40.0

    resp = await engine.analyze(
        request,
        route_weather=_route_weather(segs),
        traffic=traffic,
    )

    assert resp.status in {"ok", "partial"}
    assert len(resp.segments) == 3
    assert resp.summary.score >= 50
    assert resp.summary.risk_level in {"low", "moderate"}
    assert resp.recommendation.message


@pytest.mark.asyncio
async def test_engine_analyze_heavy_rain_heavy_traffic():
    engine = RouteIntelligenceEngine(MockRouteEngine())  # type: ignore[arg-type]
    segs = [_route_segment(i, prob=90.0) for i in range(3)]
    for i, s in enumerate(segs):
        s.arrival_time = datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc) + timedelta(minutes=i * 12)
        s.weather = _weather(precipitation_probability_pct=90, precipitation_mm=12)

    request = RouteIntelligenceRequest(
        origin=LatLng(lat=10.7, lng=106.6),
        destination=LatLng(lat=10.9, lng=106.8),
        departure_time=datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc),
        travel_mode="motorbike",
    )

    resp = await engine.analyze(
        request,
        route_weather=_route_weather(segs),
        traffic=_traffic_response(),
    )

    assert resp.summary.risk_level in {"high", "severe", "moderate"}
    assert resp.summary.worst_segment_id is not None
    assert resp.explainability.worst_segment_id == resp.summary.worst_segment_id


@pytest.mark.asyncio
async def test_engine_missing_traffic_still_works():
    engine = RouteIntelligenceEngine(MockRouteEngine())  # type: ignore[arg-type]
    segs = [_route_segment(0)]
    request = RouteIntelligenceRequest(
        origin=LatLng(lat=10.7, lng=106.6),
        destination=LatLng(lat=10.8, lng=106.7),
        departure_time=datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc),
        travel_mode="walking",
        include_traffic=False,
    )
    resp = await engine.analyze(request, route_weather=_route_weather(segs), traffic=None)
    assert resp.segments[0].traffic is None
    assert resp.status in {"ok", "partial", "unavailable"}


@pytest.mark.asyncio
async def test_engine_missing_weather_neutral_risk():
    engine = RouteIntelligenceEngine(MockRouteEngine())  # type: ignore[arg-type]
    seg = _route_segment(0)
    seg.weather = None
    rw = _route_weather([seg])
    rw.weather_status = "unavailable"

    request = RouteIntelligenceRequest(
        origin=LatLng(lat=10.7, lng=106.6),
        destination=LatLng(lat=10.8, lng=106.7),
        departure_time=datetime(2026, 8, 28, 17, 0, tzinfo=timezone.utc),
        travel_mode="motorbike",
    )
    resp = await engine.analyze(request, route_weather=rw, traffic=None)
    assert resp.summary.weather_status == "unavailable"
    assert resp.segments[0].weather.confidence < 0.5

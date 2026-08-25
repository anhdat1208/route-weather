from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.common import LatLng
from app.schemas.traffic import (
    TrafficModelInfo,
    TrafficPredictionOut,
    TrafficPredictionResponse,
    WeatherImpactInfo,
)
from app.services.traffic_service import TrafficService


def _filled_prediction() -> TrafficPredictionResponse:
    return TrafficPredictionResponse(
        generated_at=datetime(2026, 8, 25, 4, 0, tzinfo=timezone.utc),
        status="ok",
        model=TrafficModelInfo(name="baseline", version="0.1"),
        horizons=[5, 10, 15, 30],
        segments=[],
        predictions=[
            TrafficPredictionOut(
                road_segment_id="route-seg-0",
                forecast_minutes=15,
                predicted_speed_kmh=32.0,
                predicted_congestion="slow",
                confidence=0.7,
                base_prediction={
                    "speed_kmh": 32.0,
                    "congestion": "slow",
                    "speed_delta_pct": 0.0,
                },
                weather_impact=WeatherImpactInfo(
                    speed_delta_pct=0.0,
                    level="none",
                ),
                weather_adjusted={
                    "speed_kmh": 32.0,
                    "congestion": "slow",
                    "speed_delta_pct": 0.0,
                },
                model=TrafficModelInfo(name="baseline", version="0.1"),
            )
        ],
        nowcast_status="ok",
    )


@pytest.mark.asyncio
async def test_traffic_predict_endpoint_with_mock_service():
    from app.services import traffic_service as ts

    mock_response = _filled_prediction()
    service = AsyncMock()
    service.predict_for_route = AsyncMock(return_value=mock_response)
    previous = ts._traffic_service
    ts._traffic_service = service

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/traffic/prediction",
                json={
                    "geometry": [
                        {"lat": 10.4, "lng": 106.4},
                        {"lat": 10.6, "lng": 106.6},
                    ],
                },
            )
    finally:
        ts._traffic_service = previous

    assert resp.status_code == 200
    data = resp.json()
    assert data["model"]["name"] == "baseline"
    assert data["horizons"] == [5, 10, 15, 30]
    assert data["predictions"][0]["predicted_congestion"] == "slow"


@pytest.mark.asyncio
async def test_predict_for_route_survives_nowcast_failure():
    geometry = [
        LatLng(lat=10.4, lng=106.4),
        LatLng(lat=10.6, lng=106.6),
    ]
    mock_nowcast = AsyncMock()
    mock_nowcast.predict_for_route = AsyncMock(side_effect=RuntimeError("nowcast down"))

    with patch(
        "app.services.traffic_service.get_nowcasting_service",
        return_value=mock_nowcast,
    ):
        result = await TrafficService().predict_for_route(geometry, buffer_km=25.0)

    mock_nowcast.predict_for_route.assert_awaited_once_with(geometry, buffer_km=25.0)
    assert result.status == "ok"
    assert result.nowcast_status == "unavailable"
    assert len(result.segments) >= 1
    assert len(result.predictions) >= 1
    for pred in result.predictions:
        assert pred.weather_impact.speed_delta_pct == 0.0
        assert pred.weather_impact.level == "none"
    assert (
        result.message
        == "Thời tiết dự báo không khả dụng; dùng dự báo giao thông nền"
    )

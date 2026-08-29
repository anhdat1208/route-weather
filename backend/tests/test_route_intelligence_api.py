from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.common import LatLng
from app.schemas.route_intelligence import (
    RouteIntelRecommendation,
    RouteIntelSummary,
    RouteIntelligenceResponse,
    RouteIntelligenceSegment,
    SegmentRiskIntel,
    SegmentWeatherIntel,
)


def _mock_response() -> RouteIntelligenceResponse:
    now = datetime.now(timezone.utc)
    seg = RouteIntelligenceSegment(
        id="segment-1",
        index=0,
        coordinates=[LatLng(lat=10.7, lng=106.6), LatLng(lat=10.8, lng=106.7)],
        distance_m=10000,
        travel_time_seconds=600,
        arrival_time=now,
        weather=SegmentWeatherIntel(
            rain_probability_pct=10,
            rain_status="clear",
            confidence=0.9,
            source="forecast",
        ),
        risk=SegmentRiskIntel(
            weather_risk_score=15,
            weather_risk_level="low",
            traffic_risk_score=20,
            traffic_risk_level="low",
            travel_risk_score=18,
            travel_risk_level="low",
            confidence=0.85,
        ),
    )
    return RouteIntelligenceResponse(
        generated_at=now,
        status="ok",
        route={"distance_km": 10, "duration_minutes": 15},
        summary=RouteIntelSummary(
            risk_level="low",
            score=82,
            worst_segment_id="segment-1",
            worst_segment_index=0,
            worst_segment_label="Điểm xuất phát",
            weather_status="ok",
            confidence=0.85,
            eta_minutes=15,
            distance_km=10,
            weather_summary="Thời tiết thuận lợi",
            traffic_summary="Giao thông thông thoáng",
        ),
        segments=[seg],
        recommendation=RouteIntelRecommendation(message="OK", details=[]),
        explainability={
            "overall_risk_level": "low",
            "score": 82,
            "main_contributors": [],
            "weather": [],
            "traffic": [],
            "worst_segment_id": "segment-1",
            "confidence": 0.85,
        },
    )


@pytest.mark.asyncio
async def test_route_intelligence_api_analyze_structure():
    mock = AsyncMock(return_value=_mock_response())
    with patch("app.api.route_intelligence.get_route_intelligence_service") as get_svc:
        get_svc.return_value.analyze = mock
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/route-intelligence/analyze",
                json={
                    "origin": {"lat": 10.7, "lng": 106.6},
                    "destination": {"lat": 10.8, "lng": 106.7},
                    "departure_time": "2026-08-28T17:00:00+07:00",
                    "travel_mode": "motorbike",
                },
            )

    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert data["summary"]["score"] == 82
    assert data["segments"][0]["id"] == "segment-1"
    assert "recommendation" in data
    assert "explainability" in data
    mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_route_intelligence_api_compare():
    baseline = _mock_response()
    with patch("app.api.route_intelligence.get_route_intelligence_service") as get_svc:
        get_svc.return_value.compare_departures = AsyncMock(
            return_value={
                "baseline": baseline,
                "alternatives": [
                    {
                        "departure_time": baseline.generated_at.isoformat(),
                        "offset_minutes": 0,
                        "risk_level": "low",
                        "score": 82,
                    }
                ],
            }
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/route-intelligence/compare",
                json={
                    "request": {
                        "origin": {"lat": 10.7, "lng": 106.6},
                        "destination": {"lat": 10.8, "lng": 106.7},
                        "departure_time": "2026-08-28T17:00:00+07:00",
                        "travel_mode": "motorbike",
                    },
                    "offsets_minutes": [0, 30],
                },
            )

    assert resp.status_code == 200
    assert "baseline" in resp.json()

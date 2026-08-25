from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.common import LatLng
from app.schemas.nowcasting import (
    NowcastModelInfo,
    NowcastPredictionResponse,
    PredictedCellMotion,
    PredictedRainCell,
)
from app.schemas.rain_cell import CellBoundsOut, RainCellTrackResponse
from app.services.nowcasting_service import NowcastingService


def _filled_prediction() -> NowcastPredictionResponse:
    return NowcastPredictionResponse(
        generated_at=datetime(2026, 8, 25, 4, 0, tzinfo=timezone.utc),
        status="ok",
        model=NowcastModelInfo(name="baseline", version="0.1"),
        frames_used=4,
        horizons=[5, 10, 15, 30, 60],
        predictions=[
            PredictedRainCell(
                cell_id="cell-1",
                forecast_minutes=5,
                kind="predicted",
                centroid=LatLng(lat=10.5, lng=106.5),
                bounds=CellBoundsOut(
                    north=10.55,
                    south=10.45,
                    east=106.55,
                    west=106.45,
                ),
                rain_probability=0.5,
                rain_intensity=60.0,
                confidence=0.8,
                motion=PredictedCellMotion(speed_kmh=60.0, bearing_degrees=90.0),
            )
        ],
    )


@pytest.mark.asyncio
async def test_nowcasting_predict_endpoint_with_mock_service():
    from app.services import nowcasting_service as ncs

    mock_response = _filled_prediction()
    service = AsyncMock()
    service.predict_for_route = AsyncMock(return_value=mock_response)
    previous = ncs._nowcasting_service
    ncs._nowcasting_service = service

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/nowcasting/predict",
                json={
                    "geometry": [
                        {"lat": 10.4, "lng": 106.4},
                        {"lat": 10.6, "lng": 106.6},
                    ],
                },
            )
    finally:
        ncs._nowcasting_service = previous

    assert resp.status_code == 200
    data = resp.json()
    assert data["model"]["name"] == "baseline"
    assert data["horizons"] == [5, 10, 15, 30, 60]
    assert data["predictions"][0]["kind"] == "predicted"


@pytest.mark.asyncio
async def test_predict_for_route_calls_track_then_engine():
    mock_track = RainCellTrackResponse(status="ok", frames_used=3, cells=[], message=None)
    rain_svc = AsyncMock()
    rain_svc.track_for_route = AsyncMock(return_value=mock_track)
    geometry = [
        LatLng(lat=10.4, lng=106.4),
        LatLng(lat=10.6, lng=106.6),
    ]

    with patch(
        "app.services.nowcasting_service.get_rain_cell_service",
        return_value=rain_svc,
    ):
        result = await NowcastingService().predict_for_route(geometry, buffer_km=25.0)

    rain_svc.track_for_route.assert_awaited_once_with(geometry, buffer_km=25.0)
    assert result.status == "ok"
    assert result.predictions == []
    assert result.frames_used == 3
    assert result.model.name == "baseline"
    assert result.message == "Không có ô mưa đang theo dõi để dự báo."

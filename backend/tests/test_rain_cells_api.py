from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.common import LatLng
from app.schemas.rain_cell import RainCellOut, RainCellTrackResponse, TrackedRainCellOut


@pytest.mark.asyncio
async def test_rain_cells_track_endpoint_with_mock_service():
    from app.services import rain_cell_service as rcs

    mock_response = RainCellTrackResponse(
        status="ok",
        frames_used=2,
        cells=[
            TrackedRainCellOut(
                id="cell-1",
                state="TRACKING",
                current=RainCellOut(
                    id="f1",
                    timestamp="2024-06-01T12:00:00+00:00",
                    centroid=LatLng(lat=10.5, lng=106.5),
                    area_km2=12.5,
                ),
                history=[],
                missed_frames=0,
            )
        ],
    )
    service = AsyncMock()
    service.track_for_route = AsyncMock(return_value=mock_response)
    rcs._rain_cell_service = service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/rain-cells/track",
            json={
                "geometry": [
                    {"lat": 10.4, "lng": 106.4},
                    {"lat": 10.6, "lng": 106.6},
                ],
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["frames_used"] == 2
    assert len(data["cells"]) == 1

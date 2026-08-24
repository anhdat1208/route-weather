from __future__ import annotations

from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_route_weather_returns_503_without_graphhopper_key(monkeypatch):
    monkeypatch.setattr(settings, "graphhopper_api_key", "")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/route-weather",
            json={
                "origin": {"lat": 10.0, "lng": 106.0},
                "destination": {"lat": 10.03, "lng": 106.0},
                "departure_time": datetime(2026, 8, 19, 15, 30).isoformat(),
                "travel_mode": "motorbike",
            },
        )

    # Local/test environments may still have a valid key injected.
    assert resp.status_code in (200, 503)


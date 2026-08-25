from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.providers.rainviewer import RadarFrame, RainViewerProvider
from app.services.radar_service import RadarService


SAMPLE_MAPS_JSON = {
    "version": "2.0",
    "generated": 1700000000,
    "host": "https://tilecache.rainviewer.com",
    "radar": {
        "past": [
            {"time": 1699999800, "path": "/v2/radar/1699999800"},
            {"time": 1700000000, "path": "/v2/radar/1700000000"},
        ],
        "nowcast": [],
    },
}


@pytest.mark.asyncio
async def test_rainviewer_provider_parses_latest_frame():
    provider = RainViewerProvider()

    mock_resp = AsyncMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json = lambda: SAMPLE_MAPS_JSON

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.providers.rainviewer.httpx.AsyncClient", return_value=mock_client):
        frame = await provider.fetch_current_frame()

    assert frame.timestamp_unix == 1700000000
    assert frame.path == "/v2/radar/1700000000"
    assert "{z}" in frame.tile_url_template
    assert "{x}" in frame.tile_url_template
    assert "{y}" in frame.tile_url_template


@pytest.mark.asyncio
async def test_radar_service_returns_ok_status():
    frame = RadarFrame(
        timestamp_unix=int(datetime.now(timezone.utc).timestamp()) - 300,
        path="/v2/radar/1700000000",
        host="https://tilecache.rainviewer.com",
        generated_unix=1700000000,
    )
    provider = AsyncMock()
    provider.fetch_current_frame = AsyncMock(return_value=frame)
    service = RadarService(provider=provider)

    result = await service.get_current_radar()

    assert result.status == "ok"
    assert result.tile_url_template is not None
    assert result.legend is not None
    assert result.legend.provider == "rainviewer"
    assert result.legend.scheme == "universal_blue"
    # Legend must match Universal Blue tile colors (not green→red).
    stop_colors = [s.color.lower() for s in result.legend.stops]
    assert "#00a3e0" in stop_colors
    assert not any(c.startswith("#3ea7") or c.startswith("#a6f2") for c in stop_colors)


@pytest.mark.asyncio
async def test_radar_service_unavailable_on_provider_error():
    from app.providers.errors import ProviderRequestError

    provider = AsyncMock()
    provider.fetch_current_frame = AsyncMock(
        side_effect=ProviderRequestError("RainViewer radar unavailable")
    )
    service = RadarService(provider=provider)

    result = await service.get_current_radar()

    assert result.status == "unavailable"
    assert result.tile_url_template is None
    assert result.message is not None


@pytest.mark.asyncio
async def test_radar_current_endpoint():
    frame = RadarFrame(
        timestamp_unix=int(datetime.now(timezone.utc).timestamp()) - 120,
        path="/v2/radar/1700000000",
        host="https://tilecache.rainviewer.com",
        generated_unix=1700000000,
    )
    provider = AsyncMock()
    provider.fetch_current_frame = AsyncMock(return_value=frame)

    from app.services import radar_service as rs

    rs._radar_service = RadarService(provider=provider)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/radar/current")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["provider"] == "rainviewer"
    assert "tile_url_template" in data

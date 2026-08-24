from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.providers.gibs_satellite import GibsWmtsSatelliteProvider
from app.services.satellite_service import SatelliteService

SAMPLE_CAPABILITIES = """<?xml version="1.0" encoding="UTF-8"?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" xmlns:ows="http://www.opengis.net/ows/1.1">
  <Contents>
    <Layer>
      <ows:Identifier>Himawari_AHI_Band13_Clean_Infrared</ows:Identifier>
      <Dimension>
        <ows:Identifier>Time</ows:Identifier>
        <Default>2026-08-24T03:30:00Z</Default>
        <Value>2026-08-24T03:00:00Z,2026-08-24T03:10:00Z,2026-08-24T03:30:00Z</Value>
      </Dimension>
    </Layer>
  </Contents>
</Capabilities>
"""


@pytest.mark.asyncio
async def test_gibs_provider_extracts_latest_time_and_url():
    provider = GibsWmtsSatelliteProvider()
    mock_resp = AsyncMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.text = SAMPLE_CAPABILITIES

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.providers.gibs_satellite.httpx.AsyncClient", return_value=mock_client):
        frame = await provider.fetch_latest_frame()

    assert frame.observed_at == datetime(2026, 8, 24, 3, 30, tzinfo=timezone.utc)
    assert "Himawari_AHI_Band13_Clean_Infrared" in frame.tile_url_template
    assert "2026-08-24T03:30:00Z" in frame.tile_url_template


@pytest.mark.asyncio
async def test_satellite_service_marks_unavailable_on_provider_error():
    provider = AsyncMock()
    from app.providers.errors import ProviderRequestError

    provider.fetch_latest_frame = AsyncMock(side_effect=ProviderRequestError("down"))
    service = SatelliteService(provider=provider)
    response = await service.get_latest_satellite()
    assert response.status == "unavailable"
    assert response.tile_url_template is None

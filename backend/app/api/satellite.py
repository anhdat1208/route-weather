from __future__ import annotations

from fastapi import APIRouter

from app.schemas.satellite import SatelliteFrameResponse
from app.services.satellite_service import get_satellite_service

router = APIRouter(tags=["satellite"])


@router.get("/api/satellite/latest", response_model=SatelliteFrameResponse)
async def satellite_latest() -> SatelliteFrameResponse:
    """Return normalized latest satellite raster metadata for map overlay."""
    return await get_satellite_service().get_latest_satellite()

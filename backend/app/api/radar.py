from __future__ import annotations

from fastapi import APIRouter

from app.schemas.radar import RadarFrameResponse
from app.services.radar_service import get_radar_service

router = APIRouter()


@router.get("/api/radar/current", response_model=RadarFrameResponse)
async def radar_current() -> RadarFrameResponse:
    """Return normalized current precipitation radar frame metadata for map overlay."""
    return await get_radar_service().get_current_radar()

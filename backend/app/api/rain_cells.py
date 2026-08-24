from __future__ import annotations

from fastapi import APIRouter

from app.schemas.rain_cell import RainCellTrackRequest, RainCellTrackResponse
from app.services.rain_cell_service import get_rain_cell_service

router = APIRouter(tags=["rain-cells"])


@router.post("/api/rain-cells/track", response_model=RainCellTrackResponse)
async def rain_cells_track(body: RainCellTrackRequest) -> RainCellTrackResponse:
    """Detect and track precipitation cells along a route corridor."""
    return await get_rain_cell_service().track_for_route(body.geometry, buffer_km=body.buffer_km)

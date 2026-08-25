from __future__ import annotations

from app.engine.nowcasting_engine import run_nowcast
from app.schemas.common import LatLng
from app.schemas.nowcasting import NowcastPredictionResponse
from app.services.rain_cell_service import get_rain_cell_service


class NowcastingService:
    async def predict_for_route(
        self,
        geometry: list[LatLng],
        buffer_km: float | None = None,
    ) -> NowcastPredictionResponse:
        track = await get_rain_cell_service().track_for_route(
            geometry, buffer_km=buffer_km
        )
        return run_nowcast(track)


_nowcasting_service: NowcastingService | None = None


def get_nowcasting_service() -> NowcastingService:
    global _nowcasting_service
    if _nowcasting_service is None:
        _nowcasting_service = NowcastingService()
    return _nowcasting_service

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.nowcasting import NowcastPredictRequest, NowcastPredictionResponse
from app.services.nowcasting_service import get_nowcasting_service

router = APIRouter(tags=["nowcasting"])


@router.post("/api/nowcasting/predict", response_model=NowcastPredictionResponse)
async def nowcasting_predict(body: NowcastPredictRequest) -> NowcastPredictionResponse:
    """Predict rain-cell motion along a route corridor (baseline extrapolation)."""
    return await get_nowcasting_service().predict_for_route(
        body.geometry, buffer_km=body.buffer_km
    )

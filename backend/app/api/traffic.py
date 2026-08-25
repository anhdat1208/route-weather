from __future__ import annotations

from fastapi import APIRouter

from app.schemas.traffic import TrafficPredictRequest, TrafficPredictionResponse
from app.services.traffic_service import get_traffic_service

router = APIRouter(tags=["traffic"])


@router.post("/api/traffic/prediction", response_model=TrafficPredictionResponse)
async def traffic_predict(body: TrafficPredictRequest) -> TrafficPredictionResponse:
    """Predict traffic along a route corridor with optional weather impact."""
    return await get_traffic_service().predict_for_route(
        body.geometry, buffer_km=body.buffer_km
    )

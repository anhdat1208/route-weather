from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import settings
from app.engine.traffic_engine import run_traffic_prediction
from app.providers.synthetic_traffic import SyntheticTrafficProvider
from app.schemas.common import LatLng
from app.schemas.nowcasting import NowcastModelInfo, NowcastPredictionResponse
from app.schemas.traffic import TrafficPredictionResponse
from app.services.nowcasting_service import get_nowcasting_service

logger = logging.getLogger(__name__)


def _unavailable_nowcast() -> NowcastPredictionResponse:
    return NowcastPredictionResponse(
        generated_at=datetime.now(timezone.utc),
        status="unavailable",
        model=NowcastModelInfo(
            name=settings.nowcast_model_name,
            version=settings.nowcast_model_version,
        ),
        frames_used=0,
        horizons=settings.nowcast_horizons_minutes,
        predictions=[],
    )


class TrafficService:
    async def predict_for_route(
        self,
        geometry: list[LatLng],
        buffer_km: float | None = None,
    ) -> TrafficPredictionResponse:
        at = datetime.now(timezone.utc)
        segments = SyntheticTrafficProvider().current_for_route(geometry, at=at)

        try:
            nowcast = await get_nowcasting_service().predict_for_route(
                geometry, buffer_km=buffer_km
            )
        except Exception:  # noqa: BLE001 - nowcast must not fail traffic
            logger.exception(
                "Nowcast failed for traffic prediction; using unavailable fallback"
            )
            nowcast = _unavailable_nowcast()

        return run_traffic_prediction(segments, nowcast=nowcast, at=at)


_traffic_service: TrafficService | None = None


def get_traffic_service() -> TrafficService:
    global _traffic_service
    if _traffic_service is None:
        _traffic_service = TrafficService()
    return _traffic_service

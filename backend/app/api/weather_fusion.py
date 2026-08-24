from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.providers.errors import ProviderNotConfiguredError, ProviderRequestError, WeatherNotAvailableError
from app.schemas.fusion import WeatherFusionRequest, WeatherFusionResponse
from app.services.fusion_service import get_fusion_service

router = APIRouter(tags=["fusion"])


@router.post("/api/weather-fusion/state", response_model=WeatherFusionResponse)
async def weather_fusion_state(body: WeatherFusionRequest) -> WeatherFusionResponse:
    try:
        return await get_fusion_service().build_route_weather_state(body)
    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ProviderRequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except WeatherNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

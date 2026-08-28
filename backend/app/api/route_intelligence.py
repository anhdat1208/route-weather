from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.providers.errors import ProviderNotConfiguredError, ProviderRequestError, WeatherNotAvailableError
from app.schemas.route_intelligence import (
    MultiRouteCompareRequest,
    MultiRouteCompareResponse,
    RouteIntelligenceCompareRequest,
    RouteIntelligenceCompareResponse,
    RouteIntelligenceRequest,
    RouteIntelligenceResponse,
)
from app.services.route_intelligence_service import get_route_intelligence_service

router = APIRouter()


@router.post("/api/route-intelligence/analyze", response_model=RouteIntelligenceResponse)
async def route_intelligence_analyze(
    request: RouteIntelligenceRequest,
) -> RouteIntelligenceResponse:
    try:
        return await get_route_intelligence_service().analyze(request)
    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ProviderRequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except WeatherNotAvailableError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Lộ trình đã tìm được, nhưng thông tin thời tiết tạm thời không khả dụng. ({e})",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Phân tích Route Intelligence thất bại: {type(e).__name__}: {e}",
        )


@router.post("/api/route-intelligence/compare", response_model=RouteIntelligenceCompareResponse)
async def route_intelligence_compare(
    request: RouteIntelligenceCompareRequest,
) -> RouteIntelligenceCompareResponse:
    try:
        return await get_route_intelligence_service().compare_departures(request)
    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ProviderRequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="So sánh giờ xuất phát thất bại")


@router.post("/api/route-intelligence/routes/compare", response_model=MultiRouteCompareResponse)
async def route_intelligence_routes_compare(
    request: MultiRouteCompareRequest,
) -> MultiRouteCompareResponse:
    try:
        return await get_route_intelligence_service().compare_routes(request)
    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ProviderRequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="So sánh tuyến thất bại")

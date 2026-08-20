from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException

from app.engine.route_weather_engine import RouteWeatherEngine
from app.providers.errors import ProviderNotConfiguredError, ProviderRequestError, WeatherNotAvailableError
from app.providers.graphhopper import GraphHopperGeocodeProvider, GraphHopperRouteProvider
from app.providers.open_meteo import OpenMeteoProvider
from app.schemas.route_weather import (
    RouteWeatherCompareRequest,
    RouteWeatherCompareResponse,
    RouteWeatherRecommendation,
    RouteWeatherRecommendationAlternative,
    RouteWeatherResponse,
    RouteWeatherRequest,
)
from app.config import settings


router = APIRouter()


def _fmt_time(dt) -> str:
    return dt.strftime("%H:%M")


def _build_recommendation(
    *,
    baseline: RouteWeatherResponse,
    request: RouteWeatherRequest,
    alternatives: list[tuple[int, RouteWeatherResponse]],
) -> RouteWeatherRecommendation:
    current_score = baseline.risk.score

    # Exclude offset==0 when searching best alternative.
    alt_items = [(o, r) for o, r in alternatives if o != 0]
    if not alt_items:
        return RouteWeatherRecommendation(message="Dự báo tạm thời không có lựa chọn thay thế.", alternatives=[])

    best_offset, best_resp = min(alt_items, key=lambda x: x[1].risk.score)
    best_score = best_resp.risk.score

    # Not a guarantee — only based on deterministic scoring.
    if best_score <= current_score - 10:
        msg = f"Bạn có thể giảm rủi ro mưa nếu xuất phát lúc {_fmt_time(request.departure_time + timedelta(minutes=best_offset))}."
    else:
        msg = "Thay đổi giờ xuất phát có thể không tạo khác biệt rõ rệt về rủi ro mưa (ước tính)."

    alt_models: list[RouteWeatherRecommendationAlternative] = []
    for offset, resp in sorted(alternatives, key=lambda x: x[0]):
        alt_models.append(
            RouteWeatherRecommendationAlternative(
                departure_time=request.departure_time + timedelta(minutes=offset),
                risk_score=resp.risk.score,
                level=resp.risk.level,
            )
        )

    return RouteWeatherRecommendation(message=msg, alternatives=alt_models)


@router.post("/api/route-weather", response_model=RouteWeatherResponse)
async def route_weather(request: RouteWeatherRequest) -> RouteWeatherResponse:
    # Timeline labels: reverse-geocode unless explicitly disabled.
    geocode_enabled = request.geocode_route_points is not False
    if geocode_enabled and not settings.graphhopper_api_key:
        geocode_enabled = False

    try:
        route_provider = GraphHopperRouteProvider()
        weather_provider = OpenMeteoProvider()
        geocode_provider = GraphHopperGeocodeProvider() if geocode_enabled else None

        engine = RouteWeatherEngine(
            route_provider=route_provider,
            weather_provider=weather_provider,
            geocode_provider=geocode_provider,
        )

        offsets = [0, 30, 60]
        results = await engine.compute_departure_comparison(request, offsets_minutes=offsets)

        # results: list[(offset, RouteWeatherResponse)]
        baseline = next(resp for off, resp in results if off == 0)
        # Build recommendation based on those alternatives
        baseline.recommendation = _build_recommendation(
            baseline=baseline,
            request=request,
            alternatives=results,
        )
        return baseline

    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ProviderRequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except WeatherNotAvailableError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Lộ trình đã tìm được, nhưng thông tin thời tiết tạm thời không khả dụng cho thời gian đã chọn. ({e})",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tính lộ trình & thời tiết thất bại: {type(e).__name__}: {e}")


@router.post("/api/route-weather/compare", response_model=RouteWeatherCompareResponse)
async def route_weather_compare(request: RouteWeatherCompareRequest) -> RouteWeatherCompareResponse:
    req = request.request

    try:
        route_provider = GraphHopperRouteProvider()
        weather_provider = OpenMeteoProvider()

        # Disable reverse labels during compare by default for MVP performance.
        geocode_provider = None
        if bool(req.geocode_route_points) and settings.graphhopper_api_key:
            geocode_provider = GraphHopperGeocodeProvider()

        engine = RouteWeatherEngine(
            route_provider=route_provider,
            weather_provider=weather_provider,
            geocode_provider=geocode_provider,
        )

        offsets = sorted(set(request.offsets_minutes))
        if 0 not in offsets:
            offsets.insert(0, 0)

        results = await engine.compute_departure_comparison(req, offsets_minutes=offsets)
        baseline = next(resp for off, resp in results if off == 0)

        alternatives = []
        for off, resp in results:
            alternatives.append(
                {
                    "departure_time": req.departure_time + timedelta(minutes=off),
                    "risk_score": resp.risk.score,
                    "level": resp.risk.level,
                }
            )

        # Pydantic will validate response_model.
        return RouteWeatherCompareResponse(
            baseline=baseline,
            alternatives=alternatives,
        )

    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ProviderRequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except WeatherNotAvailableError:
        raise HTTPException(
            status_code=503,
            detail="Lộ trình đã tìm được, nhưng thông tin thời tiết tạm thời không khả dụng cho thời gian đã chọn.",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="So sánh giờ xuất phát thất bại")


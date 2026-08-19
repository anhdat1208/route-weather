from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.providers.errors import ProviderNotConfiguredError, ProviderRequestError
from app.providers.graphhopper import GraphHopperGeocodeProvider
from app.schemas.geocode import GeocodeSearchResponse


router = APIRouter()


@router.get("/api/geocode", response_model=GeocodeSearchResponse)
async def geocode(
    q: str = Query(..., min_length=1, description="Chuỗi địa chỉ cần tìm"),
    limit: int = Query(5, ge=1, le=20),
):
    try:
        provider = GraphHopperGeocodeProvider()
        results = await provider.search(q=q, limit=limit)
        return GeocodeSearchResponse(results=results)
    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ProviderRequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Geocoding failed")


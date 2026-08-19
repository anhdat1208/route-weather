from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng


class GeocodeResult(BaseModel):
    """Kết quả geocode từ nhà cung cấp routing/geocoding."""

    label: str = Field(..., description="Tên hiển thị (address/place name)")
    point: LatLng


class GeocodeSearchRequest(BaseModel):
    q: str = Field(..., min_length=1, description="Chuỗi địa chỉ cần tìm")
    limit: int = Field(default=5, ge=1, le=20)


class GeocodeSearchResponse(BaseModel):
    results: list[GeocodeResult]


class ReverseGeocodeRequest(BaseModel):
    point: LatLng
    radius_km: float = Field(default=2.0, ge=0.1, le=50.0)


class ReverseGeocodeResponse(BaseModel):
    result: GeocodeResult | None


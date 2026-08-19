from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


TravelMode = Literal["motorbike", "walking"]


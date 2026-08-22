from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RadarStatus = Literal["ok", "stale", "unavailable"]


class RadarLegendStop(BaseModel):
    label: str
    color: str


class RadarLegend(BaseModel):
    provider: str
    scheme: str
    title: str = "Lượng mưa"
    stops: list[RadarLegendStop]


class RadarFrameResponse(BaseModel):
    status: RadarStatus
    provider: str = "rainviewer"
    timestamp: datetime | None = None
    generated_at: datetime | None = None
    tile_url_template: str | None = None
    refresh_interval_seconds: int = Field(description="Suggested client refresh interval")
    stale_after_seconds: int = Field(description="Data older than this is considered stale")
    legend: RadarLegend | None = None
    coverage: str = "global"
    message: str | None = None

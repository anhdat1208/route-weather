from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from app.config import settings
from app.providers.errors import ProviderRequestError
from app.providers.rainviewer import RAINVIEWER_TILE_MAX_ZOOM, RainViewerProvider
from app.schemas.radar import RadarFrameResponse, RadarLegend, RadarLegendStop

logger = logging.getLogger(__name__)

# RainViewer Universal Blue (scheme 2) — sampled from official color table.
# https://www.rainviewer.com/api/color-schemes.html
# RGBA hex stripped to RGB for legend swatches.
_RAINVIEWER_LEGEND = RadarLegend(
    provider="rainviewer",
    scheme="universal_blue",
    title="Lượng mưa (radar)",
    stops=[
        RadarLegendStop(label="Rất nhẹ", color="#00a3e0"),  # ~20 dBZ cyan/blue
        RadarLegendStop(label="Nhẹ", color="#005588"),  # ~30 dBZ deep blue
        RadarLegendStop(label="Vừa", color="#ffee00"),  # ~35 dBZ yellow
        RadarLegendStop(label="Mạnh", color="#ff4400"),  # ~45 dBZ orange-red
        RadarLegendStop(label="Rất mạnh", color="#ff77ff"),  # ~60 dBZ magenta
    ],
)


class RadarService:
    """Application radar service with short-lived caching and deduplication."""

    def __init__(self, provider: RainViewerProvider | None = None) -> None:
        self._provider = provider or RainViewerProvider()
        self._cache: RadarFrameResponse | None = None
        self._cache_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_current_radar(self) -> RadarFrameResponse:
        now = time.monotonic()
        if self._cache is not None and now < self._cache_expires_at:
            return self._cache

        async with self._lock:
            now = time.monotonic()
            if self._cache is not None and now < self._cache_expires_at:
                return self._cache

            try:
                frame = await self._provider.fetch_current_frame()
            except ProviderRequestError as exc:
                logger.warning("Radar fetch failed: %s", exc)
                return RadarFrameResponse(
                    status="unavailable",
                    refresh_interval_seconds=settings.radar_refresh_interval_seconds,
                    stale_after_seconds=settings.radar_stale_after_seconds,
                    message="Dữ liệu radar tạm thời không khả dụng.",
                )

            age_seconds = max(
                0,
                int(datetime.now(timezone.utc).timestamp() - frame.timestamp_unix),
            )
            status = "ok"
            if age_seconds > settings.radar_stale_after_seconds:
                status = "stale"

            generated_at = (
                datetime.fromtimestamp(frame.generated_unix, tz=timezone.utc)
                if frame.generated_unix is not None
                else None
            )

            response = RadarFrameResponse(
                status=status,
                timestamp=frame.timestamp,
                generated_at=generated_at,
                tile_url_template=frame.tile_url_template,
                tile_max_zoom=RAINVIEWER_TILE_MAX_ZOOM,
                refresh_interval_seconds=settings.radar_refresh_interval_seconds,
                stale_after_seconds=settings.radar_stale_after_seconds,
                legend=_RAINVIEWER_LEGEND,
                coverage="global",
                message=(
                    "Dữ liệu radar có thể đã cũ."
                    if status == "stale"
                    else None
                ),
            )

            self._cache = response
            self._cache_expires_at = time.monotonic() + settings.cache_ttl_radar
            return response


_radar_service: RadarService | None = None


def get_radar_service() -> RadarService:
    global _radar_service
    if _radar_service is None:
        _radar_service = RadarService()
    return _radar_service

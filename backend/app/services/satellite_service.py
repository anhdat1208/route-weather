from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from app.config import settings
from app.providers.errors import ProviderRequestError
from app.providers.gibs_satellite import GibsWmtsSatelliteProvider
from app.schemas.satellite import SatelliteFrameResponse

logger = logging.getLogger(__name__)


class SatelliteService:
    def __init__(self, provider: GibsWmtsSatelliteProvider | None = None) -> None:
        self._provider = provider or GibsWmtsSatelliteProvider()
        self._cache: SatelliteFrameResponse | None = None
        self._cache_expires_at = 0.0
        self._lock = asyncio.Lock()

    async def get_latest_satellite(self) -> SatelliteFrameResponse:
        now = time.monotonic()
        if self._cache is not None and now < self._cache_expires_at:
            return self._cache

        async with self._lock:
            now = time.monotonic()
            if self._cache is not None and now < self._cache_expires_at:
                return self._cache

            received_at = datetime.now(timezone.utc)
            try:
                frame = await self._provider.fetch_latest_frame()
            except ProviderRequestError as exc:
                logger.warning("Satellite fetch failed: %s", exc)
                return SatelliteFrameResponse(
                    status="unavailable",
                    provider=settings.satellite_provider_name,
                    source="nasa_gibs",
                    refresh_interval_seconds=settings.satellite_refresh_interval_seconds,
                    stale_after_seconds=settings.satellite_stale_after_seconds,
                    message="Dữ liệu vệ tinh tạm thời không khả dụng.",
                )

            age_seconds = max(0, int((received_at - frame.observed_at).total_seconds()))
            status = "stale" if age_seconds > settings.satellite_stale_after_seconds else "ok"

            response = SatelliteFrameResponse(
                status=status,
                provider=settings.satellite_provider_name,
                source=frame.source,
                timestamp=frame.observed_at,
                observed_at=frame.observed_at,
                received_at=received_at,
                tile_url_template=frame.tile_url_template,
                tile_matrix_set=frame.tile_matrix_set,
                tile_format=frame.tile_format,
                tile_max_zoom=settings.gibs_tile_max_zoom,
                refresh_interval_seconds=settings.satellite_refresh_interval_seconds,
                stale_after_seconds=settings.satellite_stale_after_seconds,
                message="Dữ liệu vệ tinh có thể đã cũ." if status == "stale" else None,
            )
            self._cache = response
            self._cache_expires_at = time.monotonic() + settings.cache_ttl_satellite
            return response


_satellite_service: SatelliteService | None = None


def get_satellite_service() -> SatelliteService:
    global _satellite_service
    if _satellite_service is None:
        _satellite_service = SatelliteService()
    return _satellite_service

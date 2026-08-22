from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.providers.errors import ProviderRequestError

logger = logging.getLogger(__name__)

# RainViewer color scheme 2 = Universal Blue precipitation scale.
# https://www.rainviewer.com/api.html
RAINVIEWER_COLOR_SCHEME = 2
RAINVIEWER_TILE_OPTIONS = "1_0"  # no smoothing/snow extras (free tier compatible)
RAINVIEWER_TILE_MAX_ZOOM = 7  # https://www.rainviewer.com/api/weather-maps-api.html


@dataclass(frozen=True)
class RadarFrame:
    timestamp_unix: int
    path: str
    host: str
    generated_unix: int | None

    @property
    def timestamp(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp_unix, tz=timezone.utc)

    @property
    def tile_url_template(self) -> str:
        return (
            f"{self.host}{self.path}/256/{{z}}/{{x}}/{{y}}/"
            f"{RAINVIEWER_COLOR_SCHEME}/{RAINVIEWER_TILE_OPTIONS}.png"
        )


class RainViewerProvider:
    """Adapter for RainViewer public weather-maps API."""

    def __init__(self, *, base_url: str | None = None, timeout: float = 15.0) -> None:
        self._base_url = (base_url or settings.rainviewer_api_url).rstrip("/")
        self._timeout = timeout

    async def fetch_current_frame(self) -> RadarFrame:
        url = f"{self._base_url}/public/weather-maps.json"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                payload: dict[str, Any] = resp.json()
        except httpx.HTTPError as exc:
            logger.warning("RainViewer request failed: %s", exc)
            raise ProviderRequestError(f"RainViewer radar unavailable: {exc}") from exc

        host = str(payload.get("host", "https://tilecache.rainviewer.com")).rstrip("/")
        generated = payload.get("generated")
        generated_unix = int(generated) if generated is not None else None

        radar = payload.get("radar") or {}
        past: list[dict[str, Any]] = radar.get("past") or []
        if not past:
            raise ProviderRequestError("RainViewer returned no radar frames")

        latest = past[-1]
        timestamp_unix = int(latest["time"])
        path = str(latest["path"])

        return RadarFrame(
            timestamp_unix=timestamp_unix,
            path=path,
            host=host,
            generated_unix=generated_unix,
        )

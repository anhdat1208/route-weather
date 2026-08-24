from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from app.config import settings
from app.providers.errors import ProviderRequestError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SatelliteFrame:
    observed_at: datetime
    tile_url_template: str
    layer: str
    tile_matrix_set: str
    tile_format: str
    source: str = "nasa_gibs"


class GibsWmtsSatelliteProvider:
    """Adapter for NASA GIBS WMTS time-enabled raster layers."""

    def __init__(
        self,
        *,
        capabilities_url: str | None = None,
        layer: str | None = None,
        tile_matrix_set: str | None = None,
        tile_format: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        self._capabilities_url = capabilities_url or settings.gibs_wmts_capabilities_url
        self._layer = layer or settings.gibs_satellite_layer
        self._tile_matrix_set = tile_matrix_set or settings.gibs_tile_matrix_set
        self._tile_format = tile_format or settings.gibs_tile_format
        self._timeout = timeout
        self._cache_xml: str | None = None
        self._cache_expires_at = 0.0

    async def fetch_latest_frame(self) -> SatelliteFrame:
        xml_text = await self._fetch_capabilities_xml()
        observed_at = self._extract_latest_time(xml_text, self._layer)
        tile_url = self._build_wmts_template(observed_at)
        return SatelliteFrame(
            observed_at=observed_at,
            tile_url_template=tile_url,
            layer=self._layer,
            tile_matrix_set=self._tile_matrix_set,
            tile_format=self._tile_format,
        )

    async def _fetch_capabilities_xml(self) -> str:
        now = time.monotonic()
        if self._cache_xml is not None and now < self._cache_expires_at:
            return self._cache_xml

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._capabilities_url)
                resp.raise_for_status()
                xml_text = resp.text
        except httpx.HTTPError as exc:
            logger.warning("GIBS capabilities fetch failed: %s", exc)
            raise ProviderRequestError(f"GIBS satellite unavailable: {exc}") from exc

        self._cache_xml = xml_text
        self._cache_expires_at = now + settings.cache_ttl_satellite
        return xml_text

    def _extract_latest_time(self, capabilities_xml: str, layer_name: str) -> datetime:
        ns = {
            "wmts": "http://www.opengis.net/wmts/1.0",
            "ows": "http://www.opengis.net/ows/1.1",
        }
        try:
            root = ET.fromstring(capabilities_xml)
        except ET.ParseError as exc:
            raise ProviderRequestError(f"GIBS capabilities parse failed: {exc}") from exc

        layer_nodes = root.findall(".//wmts:Layer", ns)
        target_layer: ET.Element | None = None
        for layer in layer_nodes:
            identifier = layer.find("ows:Identifier", ns)
            if identifier is not None and (identifier.text or "").strip() == layer_name:
                target_layer = layer
                break
        if target_layer is None:
            raise ProviderRequestError(f"GIBS layer not found in capabilities: {layer_name}")

        dimension_values: list[str] = []
        for dim in target_layer.findall("wmts:Dimension", ns):
            dim_id = dim.find("ows:Identifier", ns)
            if dim_id is None or (dim_id.text or "").strip().lower() != "time":
                continue
            value_nodes = dim.findall("wmts:Value", ns)
            for node in value_nodes:
                if node.text:
                    dimension_values.append(node.text.strip())
            default_node = dim.find("wmts:Default", ns)
            if default_node is not None and default_node.text:
                dimension_values.append(default_node.text.strip())

        if not dimension_values:
            raise ProviderRequestError("GIBS Time dimension not found for selected layer")

        candidates: list[datetime] = []
        for raw in dimension_values:
            for token in raw.split(","):
                ts = self._parse_time_token(token.strip())
                if ts is not None:
                    candidates.append(ts)
        if not candidates:
            raise ProviderRequestError("GIBS Time dimension has no parseable values")
        return max(candidates)

    def _parse_time_token(self, token: str) -> datetime | None:
        # Supports plain date, datetime, and range form: start/end/period.
        if not token:
            return None
        if "/" in token:
            parts = token.split("/")
            if len(parts) >= 2:
                return self._parse_time_token(parts[1]) or self._parse_time_token(parts[0])
            return None
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
            return datetime.fromisoformat(f"{token}T00:00:00+00:00")
        normalized = token.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    def _build_wmts_template(self, observed_at: datetime) -> str:
        time_part = observed_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ext = self._tile_format
        # WMTS template for GIBS EPSG:3857 "best" endpoint.
        return (
            f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{self._layer}/default/"
            f"{time_part}/{self._tile_matrix_set}/{{z}}/{{y}}/{{x}}.{ext}"
        )

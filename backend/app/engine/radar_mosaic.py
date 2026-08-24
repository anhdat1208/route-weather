from __future__ import annotations

import logging

import httpx

from app.engine.radar_intensity import decode_rainviewer_intensity_png
from app.engine.radar_models import INVALID_INTENSITY, IntensityGrid, RadarBounds, RadarFrame
from app.engine.radar_tile_math import tile_range_for_bounds, tile_xy_bounds
from app.providers.rainviewer import RAINVIEWER_TILE_MAX_ZOOM, RadarFrame as ProviderFrame

logger = logging.getLogger(__name__)

TILE_SIZE = 256
# Raw-ish grayscale tiles for detection (separate from Stage 2 display palette).
DETECTION_COLOR_SCHEME = 0
DETECTION_TILE_OPTIONS = "0_0"


async def build_radar_frame_from_tiles(
    *,
    provider_frame: ProviderFrame,
    bounds: RadarBounds,
    zoom: int,
    client: httpx.AsyncClient | None = None,
) -> RadarFrame | None:
    zoom = min(max(1, zoom), RAINVIEWER_TILE_MAX_ZOOM)
    x_min, x_max, y_min, y_max = tile_range_for_bounds(bounds, zoom)
    tile_cols = x_max - x_min + 1
    tile_rows = y_max - y_min + 1
    width = tile_cols * TILE_SIZE
    height = tile_rows * TILE_SIZE

    grid = IntensityGrid.empty(width, height, bounds)
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=20.0)

    assert client is not None
    try:
        for ty in range(y_min, y_max + 1):
            for tx in range(x_min, x_max + 1):
                url = (
                    f"{provider_frame.host}{provider_frame.path}/{TILE_SIZE}/"
                    f"{zoom}/{tx}/{ty}/{DETECTION_COLOR_SCHEME}/{DETECTION_TILE_OPTIONS}.png"
                )
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        logger.debug("Tile miss %s status=%s", url, resp.status_code)
                        continue
                    tile_values = decode_rainviewer_intensity_png(resp.content)
                except httpx.HTTPError as exc:
                    logger.debug("Tile fetch failed %s: %s", url, exc)
                    continue

                row_offset = (ty - y_min) * TILE_SIZE
                col_offset = (tx - x_min) * TILE_SIZE
                for row in range(TILE_SIZE):
                    for col in range(TILE_SIZE):
                        idx = row * TILE_SIZE + col
                        if idx >= len(tile_values):
                            continue
                        val = tile_values[idx]
                        if val != val:  # NaN
                            continue
                        grid.set(row_offset + row, col_offset + col, val)
    finally:
        if own_client:
            await client.aclose()

    # Trim grid bounds to actual tile coverage for accurate georeferencing.
    nw = tile_xy_bounds(zoom, x_min, y_min)
    se = tile_xy_bounds(zoom, x_max, y_max)
    grid.bounds = RadarBounds(north=nw.north, south=se.south, east=se.east, west=nw.west)

    if not _has_valid_pixels(grid):
        return None

    return RadarFrame(timestamp=provider_frame.timestamp, grid=grid)


def build_radar_frame_from_grid(
    *,
    values: list[list[float]],
    bounds: RadarBounds,
    timestamp,
) -> RadarFrame:
    """Build a RadarFrame from a synthetic 2D grid (tests only)."""

    height = len(values)
    width = len(values[0]) if height else 0
    flat: list[float] = []
    for row in values:
        for v in row:
            flat.append(float(v) if v > 0 else INVALID_INTENSITY)
    grid = IntensityGrid(width=width, height=height, values=flat, bounds=bounds)
    return RadarFrame(timestamp=timestamp, grid=grid)


def _has_valid_pixels(grid: IntensityGrid) -> bool:
    for v in grid.values:
        if v == v and v > 0:  # not NaN
            return True
    return False

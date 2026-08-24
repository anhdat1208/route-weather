from __future__ import annotations

import uuid

from app.engine.radar_models import (
    CellIntensityStats,
    INVALID_INTENSITY,
    RadarBounds,
    RadarFrame,
    RainCellDetection,
)


def detect_cells_in_frame(
    frame: RadarFrame,
    *,
    min_intensity: float,
    min_area_pixels: int,
    max_area_pixels: int,
) -> list[RainCellDetection]:
    grid = frame.grid
    w, h = grid.width, grid.height
    visited = [False] * (w * h)
    detections: list[RainCellDetection] = []

    for row in range(h):
        for col in range(w):
            idx = row * w + col
            if visited[idx]:
                continue
            val = grid.get(row, col)
            if val != val or val < min_intensity:  # NaN or below threshold
                visited[idx] = True
                continue

            component = _flood_fill(grid, row, col, min_intensity, visited)
            if len(component) < min_area_pixels or len(component) > max_area_pixels:
                continue

            det = _component_to_detection(frame, component)
            detections.append(det)

    return detections


def _flood_fill(grid, start_row, start_col, min_intensity, visited):
    w, h = grid.width, grid.height
    stack = [(start_row, start_col)]
    component: list[tuple[int, int]] = []

    while stack:
        row, col = stack.pop()
        idx = row * w + col
        if row < 0 or col < 0 or row >= h or col >= w or visited[idx]:
            continue
        val = grid.get(row, col)
        if val != val or val < min_intensity:
            visited[idx] = True
            continue
        visited[idx] = True
        component.append((row, col))
        stack.extend([(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)])

    return component


def _component_to_detection(frame: RadarFrame, pixels: list[tuple[int, int]]) -> RainCellDetection:
    grid = frame.grid
    intensities: list[float] = []
    rows = [p[0] for p in pixels]
    cols = [p[1] for p in pixels]
    area_km2 = 0.0
    for row, col in pixels:
        val = grid.get(row, col)
        if val == val:
            intensities.append(val)
        area_km2 += grid.pixel_area_km2(row, col)

    mean_i = sum(intensities) / len(intensities) if intensities else None
    stats = CellIntensityStats(
        min=min(intensities) if intensities else None,
        max=max(intensities) if intensities else None,
        mean=mean_i,
    )

    lat_sum = 0.0
    lng_sum = 0.0
    for row, col in pixels:
        p = grid.pixel_to_lat_lng(row, col)
        lat_sum += p.lat
        lng_sum += p.lng
    n = len(pixels)
    centroid = grid.pixel_to_lat_lng(
        int(sum(rows) / n),
        int(sum(cols) / n),
    )

    north = max(grid.pixel_to_lat_lng(r, c).lat for r, c in pixels)
    south = min(grid.pixel_to_lat_lng(r, c).lat for r, c in pixels)
    east = max(grid.pixel_to_lat_lng(r, c).lng for r, c in pixels)
    west = min(grid.pixel_to_lat_lng(r, c).lng for r, c in pixels)

    return RainCellDetection(
        frame_id=str(uuid.uuid4()),
        timestamp=frame.timestamp,
        centroid=centroid,
        area_km2=round(area_km2, 3),
        area_pixels=len(pixels),
        intensity=stats,
        bounds=RadarBounds(north=north, south=south, east=east, west=west),
        pixels=pixels,
    )

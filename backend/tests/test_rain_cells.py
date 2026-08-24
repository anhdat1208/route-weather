from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.engine.geo_math import initial_bearing_deg
from app.engine.radar_models import (
    CellIntensityStats,
    RadarBounds,
    RainCellDetection,
)
from app.engine.radar_mosaic import build_radar_frame_from_grid
from app.engine.rain_cell_detect import detect_cells_in_frame
from app.engine.rain_cell_track import track_rain_cells
from app.schemas.common import LatLng

T0 = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(minutes=10)
BOUNDS = RadarBounds(north=11.0, south=10.0, east=107.0, west=106.0)


def _detect(grid: list[list[float]], ts: datetime = T0):
    frame = build_radar_frame_from_grid(values=grid, bounds=BOUNDS, timestamp=ts)
    return detect_cells_in_frame(
        frame,
        min_intensity=25.0,
        min_area_pixels=4,
        max_area_pixels=10_000,
    )


def test_single_cell_detection():
    grid = [
        [0, 0, 0, 0],
        [0, 50, 50, 0],
        [0, 50, 50, 0],
        [0, 0, 0, 0],
    ]
    detections = _detect(grid)
    assert len(detections) == 1
    assert detections[0].area_pixels == 4


def test_multiple_cells_detection():
    grid = [
        [50, 50, 0, 0, 50, 50],
        [50, 50, 0, 0, 50, 50],
        [0, 0, 0, 0, 0, 0],
    ]
    detections = _detect(grid)
    assert len(detections) == 2


def test_noise_filtering():
    grid = [
        [0, 30, 0],
        [0, 0, 0],
    ]
    detections = _detect(grid)
    assert len(detections) == 0


def test_cell_tracking_preserves_identity():
    grid_t0 = [
        [0, 0, 0, 0, 0],
        [0, 50, 50, 0, 0],
        [0, 50, 50, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    grid_t1 = [
        [0, 0, 0, 0, 0],
        [0, 0, 50, 50, 0],
        [0, 0, 50, 50, 0],
        [0, 0, 0, 0, 0],
    ]
    f0 = build_radar_frame_from_grid(values=grid_t0, bounds=BOUNDS, timestamp=T0)
    f1 = build_radar_frame_from_grid(values=grid_t1, bounds=BOUNDS, timestamp=T1)
    d0 = detect_cells_in_frame(f0, min_intensity=25, min_area_pixels=4, max_area_pixels=10_000)
    d1 = detect_cells_in_frame(f1, min_intensity=25, min_area_pixels=4, max_area_pixels=10_000)

    tracked = track_rain_cells(
        [(f0, d0), (f1, d1)],
        max_match_distance_km=80,
        history_frames=6,
        max_missed_frames=2,
    )
    assert len(tracked) == 1
    assert tracked[0].state == "TRACKING"
    assert len(tracked[0].history) == 1


def test_cell_movement_speed_and_bearing():
    centroid_a = LatLng(lat=10.5, lng=106.5)
    centroid_b = LatLng(lat=10.5, lng=106.6)
    det_a = RainCellDetection(
        frame_id="a",
        timestamp=T0,
        centroid=centroid_a,
        area_km2=10.0,
        area_pixels=100,
        intensity=CellIntensityStats(min=40, max=60, mean=50),
        bounds=BOUNDS,
    )
    det_b = RainCellDetection(
        frame_id="b",
        timestamp=T1,
        centroid=centroid_b,
        area_km2=10.0,
        area_pixels=100,
        intensity=CellIntensityStats(min=40, max=60, mean=50),
        bounds=BOUNDS,
    )
    f0 = build_radar_frame_from_grid(values=[[50]], bounds=BOUNDS, timestamp=T0)
    f1 = build_radar_frame_from_grid(values=[[50]], bounds=BOUNDS, timestamp=T1)

    tracked = track_rain_cells(
        [(f0, [det_a]), (f1, [det_b])],
        max_match_distance_km=80,
        history_frames=6,
        max_missed_frames=2,
    )
    assert tracked[0].motion is not None
    assert tracked[0].motion.speed_kmh is not None
    assert tracked[0].motion.speed_kmh > 0
    bearing = initial_bearing_deg(centroid_a, centroid_b)
    assert tracked[0].motion.bearing_degrees == pytest.approx(bearing, abs=1.0)


def test_cell_disappearance_goes_lost():
    grid = [
        [0, 50, 50, 0],
        [0, 50, 50, 0],
    ]
    empty = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    f0 = build_radar_frame_from_grid(values=grid, bounds=BOUNDS, timestamp=T0)
    f1 = build_radar_frame_from_grid(values=empty, bounds=BOUNDS, timestamp=T1)
    d0 = detect_cells_in_frame(f0, min_intensity=25, min_area_pixels=4, max_area_pixels=10_000)

    tracked = track_rain_cells(
        [(f0, d0), (f1, [])],
        max_match_distance_km=80,
        history_frames=6,
        max_missed_frames=2,
    )
    assert any(t.state == "LOST" for t in tracked)


def test_new_cell_gets_new_identity():
    grid_a = [
        [50, 50, 0, 0],
        [50, 50, 0, 0],
    ]
    grid_b = [
        [0, 0, 50, 50],
        [0, 0, 50, 50],
    ]
    f0 = build_radar_frame_from_grid(values=grid_a, bounds=BOUNDS, timestamp=T0)
    f1 = build_radar_frame_from_grid(values=grid_b, bounds=BOUNDS, timestamp=T1)
    d0 = detect_cells_in_frame(f0, min_intensity=25, min_area_pixels=4, max_area_pixels=10_000)
    d1 = detect_cells_in_frame(f1, min_intensity=25, min_area_pixels=4, max_area_pixels=10_000)

    tracked = track_rain_cells(
        [(f0, d0), (f1, d1)],
        max_match_distance_km=5,
        history_frames=6,
        max_missed_frames=2,
    )
    assert len(tracked) == 2
    ids = {t.id for t in tracked}
    assert len(ids) == 2

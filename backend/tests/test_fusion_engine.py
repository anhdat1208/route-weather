from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import settings
from app.engine.fusion_engine import fuse_weather_state
from tests.fixtures.synthetic_weather_sources import (
    distant_rain_cell,
    synthetic_radar,
    synthetic_rain_cells,
    synthetic_route_weather,
    synthetic_satellite,
)


def test_fusion_all_sources_available():
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(),
        satellite=synthetic_satellite(),
        rain_cells=synthetic_rain_cells(),
    )
    assert len(fused.segments) == 2
    assert fused.segments[0].data_quality.radar in ("GOOD", "CONFLICTING")
    assert fused.segments[0].satellite_meta is not None
    assert fused.segments[0].rain_cell is not None


def test_fusion_missing_satellite():
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(),
        satellite=None,
        rain_cells=synthetic_rain_cells(),
    )
    assert fused.segments[0].data_quality.satellite == "MISSING"
    assert fused.segments[0].satellite_meta is None


def test_fusion_stale_satellite():
    old = datetime.now(timezone.utc) - timedelta(seconds=settings.satellite_stale_after_seconds + 600)
    sat = synthetic_satellite(ts=old, status="stale").model_copy(update={"received_at": datetime.now(timezone.utc)})
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=None,
        satellite=sat,
        rain_cells=synthetic_rain_cells(),
    )
    assert fused.segments[0].data_quality.satellite == "STALE"


def test_fusion_conflicting_observation_times():
    radar_ts = datetime(2026, 8, 24, 3, 40, tzinfo=timezone.utc)
    sat_ts = radar_ts - timedelta(seconds=settings.fusion_alignment_max_seconds + 600)
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(ts=radar_ts),
        satellite=synthetic_satellite(ts=sat_ts),
        rain_cells=synthetic_rain_cells(),
    )
    assert "radar_satellite_time_mismatch" in fused.segments[0].data_quality.conflicts
    assert fused.segments[0].data_quality.radar == "CONFLICTING"
    assert fused.segments[0].data_quality.satellite == "CONFLICTING"


def test_fusion_preserves_source_timestamps():
    radar_ts = datetime(2026, 8, 24, 3, 40, tzinfo=timezone.utc)
    sat_ts = datetime(2026, 8, 24, 3, 30, tzinfo=timezone.utc)
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(ts=radar_ts),
        satellite=synthetic_satellite(ts=sat_ts),
        rain_cells=synthetic_rain_cells(),
    )
    assert fused.segments[0].radar_meta is not None
    assert fused.segments[0].satellite_meta is not None
    assert fused.segments[0].radar_meta.observed_at == radar_ts
    assert fused.segments[0].satellite_meta.observed_at == sat_ts


def test_fusion_route_association():
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(),
        satellite=synthetic_satellite(),
        rain_cells=synthetic_rain_cells(),
    )
    counts = [seg.rain_cell.count if seg.rain_cell else 0 for seg in fused.segments]
    assert any(c > 0 for c in counts)


def test_fusion_corridor_ignores_distant_cells():
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(),
        satellite=synthetic_satellite(),
        rain_cells=synthetic_rain_cells(extra_cells=[distant_rain_cell()]),
    )
    associated_ids = sum(seg.rain_cell.count if seg.rain_cell else 0 for seg in fused.segments)
    assert associated_ids == 1
    assert fused.segments[0].rain_cell is not None
    assert fused.segments[0].rain_cell.count == 1
    assert fused.segments[1].rain_cell is None or fused.segments[1].rain_cell.count == 0


def test_fusion_segment_features_and_confidence():
    fused = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(),
        satellite=synthetic_satellite(),
        rain_cells=synthetic_rain_cells(),
    )
    seg = fused.segments[0]
    assert seg.features.precip_probability_pct == 30
    assert seg.features.rain_cell_count == 1
    assert seg.features.precip_evidence is True
    assert seg.features.radar_available is True
    assert seg.features.satellite_available is True
    assert 0.5 <= seg.confidence <= 1.0


def test_fusion_confidence_drops_when_sources_missing():
    full = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=synthetic_radar(),
        satellite=synthetic_satellite(),
        rain_cells=synthetic_rain_cells(),
    )
    sparse = fuse_weather_state(
        route_weather=synthetic_route_weather(),
        radar=None,
        satellite=None,
        rain_cells=None,
    )
    assert sparse.segments[0].confidence < full.segments[0].confidence
    assert sparse.segments[0].features.precip_evidence is False

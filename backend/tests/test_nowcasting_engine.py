from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings
from app.engine.nowcasting_engine import run_nowcast
from app.schemas.common import LatLng
from app.schemas.rain_cell import (
    CellBoundsOut,
    CellIntensityOut,
    CellMotionOut,
    RainCellOut,
    RainCellTrackResponse,
    TrackedRainCellOut,
)

ORIGIN = LatLng(lat=10.0, lng=106.0)
BOUNDS = CellBoundsOut(north=10.05, south=9.95, east=106.05, west=105.95)
GENERATED_AT = datetime(2026, 8, 25, 4, 0, tzinfo=timezone.utc)


def _cell(
    *,
    cell_id: str = "c1",
    state: str = "TRACKING",
    speed_kmh: float | None = 60.0,
    bearing_degrees: float | None = 90.0,
    include_motion: bool = True,
) -> TrackedRainCellOut:
    motion = None
    if include_motion:
        motion = CellMotionOut(
            speed_kmh=speed_kmh,
            bearing_degrees=bearing_degrees,
            from_point=ORIGIN,
            to_point=ORIGIN,
            confidence=1.0,
        )
    return TrackedRainCellOut(
        id=cell_id,
        state=state,  # type: ignore[arg-type]
        current=RainCellOut(
            id=f"{cell_id}-now",
            timestamp="2026-08-25T04:00:00+00:00",
            centroid=ORIGIN,
            area_km2=12.0,
            intensity=CellIntensityOut(min=50.0, max=70.0, mean=60.0),
            bounds=BOUNDS,
        ),
        history=[],
        motion=motion,
        missed_frames=0,
    )


def _track(
    *,
    status: str = "ok",
    frames_used: int = 4,
    cells: list[TrackedRainCellOut] | None = None,
    message: str | None = None,
) -> RainCellTrackResponse:
    return RainCellTrackResponse(
        status=status,  # type: ignore[arg-type]
        frames_used=frames_used,
        cells=cells if cells is not None else [],
        message=message,
    )


def test_engine_unavailable_passthrough():
    track = _track(
        status="unavailable",
        frames_used=0,
        cells=[_cell()],
        message="Radar đang bảo trì.",
    )
    result = run_nowcast(track, generated_at=GENERATED_AT)

    assert result.status == "unavailable"
    assert result.predictions == []
    assert result.message == "Radar đang bảo trì."
    assert result.frames_used == 0
    assert result.horizons == list(settings.nowcast_horizons_minutes)
    assert result.model.name == settings.nowcast_model_name
    assert result.model.version == settings.nowcast_model_version
    assert result.radar_age_seconds is None
    assert result.generated_at == GENERATED_AT


def test_engine_unavailable_uses_vietnamese_default():
    track = _track(status="unavailable", frames_used=1, message=None)
    result = run_nowcast(track, generated_at=GENERATED_AT)

    assert result.status == "unavailable"
    assert result.predictions == []
    assert result.message == "Dữ liệu theo dõi ô mưa tạm thời không khả dụng."


def test_engine_empty_cells_ok_with_message():
    track = _track(status="ok", frames_used=3, cells=[], message=None)
    result = run_nowcast(track, generated_at=GENERATED_AT)

    assert result.status == "ok"
    assert result.predictions == []
    assert result.message == "Không có ô mưa đang theo dõi để dự báo."
    assert result.frames_used == 3
    assert result.horizons == list(settings.nowcast_horizons_minutes)
    assert result.model.name == settings.nowcast_model_name
    assert result.model.version == settings.nowcast_model_version


def test_engine_runs_baseline_and_sets_model_info():
    track = _track(status="ok", frames_used=4, cells=[_cell()])
    result = run_nowcast(track, generated_at=GENERATED_AT, radar_age_seconds=120)

    assert result.status == "ok"
    assert result.message is None
    assert result.generated_at == GENERATED_AT
    assert result.frames_used == 4
    assert result.radar_age_seconds == 120
    assert result.horizons == [5, 10, 15, 30, 60]
    assert result.model.name == "baseline"
    assert result.model.version == "0.1"
    assert len(result.predictions) == 5
    assert {p.forecast_minutes for p in result.predictions} == {5, 10, 15, 30, 60}
    assert all(p.kind == "predicted" for p in result.predictions)
    assert all(p.cell_id == "c1" for p in result.predictions)


def test_engine_partial_when_track_partial():
    track = _track(
        status="partial",
        frames_used=2,
        cells=[_cell()],
        message="Một số khung radar không khả dụng.",
    )
    result = run_nowcast(track, generated_at=GENERATED_AT)

    assert result.status == "partial"
    assert result.predictions
    assert result.message == "Một số khung radar không khả dụng."
    assert result.frames_used == 2


def test_engine_partial_when_missing_motion():
    track = _track(
        status="ok",
        frames_used=4,
        cells=[_cell(speed_kmh=None, bearing_degrees=90.0)],
    )
    result = run_nowcast(track, generated_at=GENERATED_AT)

    assert result.status == "partial"
    assert result.predictions
    assert any(p.confidence < 0.35 for p in result.predictions)
    assert result.message == "Một số ô mưa thiếu vector chuyển động nên dự báo chưa đầy đủ."

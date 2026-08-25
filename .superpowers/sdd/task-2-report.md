# Task 2 Report: BaselineExtrapolationModel (TDD core)

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE

## Summary

Implemented the Stage 5 baseline nowcasting model: `NowcastingModel` protocol plus `BaselineExtrapolationModel` that extrapolates tracked rain cells along motion vectors for horizons 5/10/15/30/60 minutes. Intensity uses a linear trend from history+current means (fallback to current mean). Confidence applies the locked decay factors. No engine, service, API, or frontend (out of scope).

## TDD Evidence

### RED — Step 1–2: Failing tests first

Created `backend/tests/test_nowcasting_baseline.py` with the 11 named tests from the brief (fixtures for `TrackedRainCellOut` + motion + history). Production module did not exist yet.

```text
$ cd backend; python -m pytest tests/test_nowcasting_baseline.py -v

ERROR collecting tests/test_nowcasting_baseline.py
ImportError while importing test module '.../tests/test_nowcasting_baseline.py'.
tests\test_nowcasting_baseline.py:9: in <module>
    from app.engine.nowcasting_models import BaselineExtrapolationModel
E   ModuleNotFoundError: No module named 'app.engine.nowcasting_models'
============================== 1 error in 0.55s ===============================
```

Failure reason matches expectation: `nowcasting_models` not yet implemented.

### GREEN — Step 3–4: Minimal implementation

Added `backend/app/engine/nowcasting_models.py`:

- `NowcastingModel` protocol (`predict`)
- `BaselineExtrapolationModel` with `name`/`version` from settings
- Eligible states: `TRACKING`, `NEW` only (`LOST`/`EXPIRED` omitted)
- Distance km = `speed_kmh * (forecast_minutes / 60)`; `destination_point` for centroid; bounds translated by the same lat/lng delta
- Missing speed or bearing: hold centroid/bounds; `×0.5` then cap confidence ≤ 0.35
- Intensity: least-squares slope vs minutes when ≥2 timestamped means (history+current); else current mean; clamp `[0, nowcast_intensity_max]`
- `rain_probability = clamp(intensity / nowcast_intensity_max, 0, 1)` (None if intensity None)
- Confidence: base `motion.confidence` or `0.4` × horizon `max(0.25, 1 - minutes/90)` ×0.7 short frames ×0.75 short history ×0.5 missing vector ×0.6 stale radar; clamp `[0, 1]`
- `source="rain_cell_track+baseline"`; motion copied from input speed/bearing

```text
$ cd backend; python -m pytest tests/test_nowcasting_baseline.py -v

tests/test_nowcasting_baseline.py::test_horizons_emit_five_predictions_per_cell PASSED
tests/test_nowcasting_baseline.py::test_projects_centroid_with_speed_and_bearing PASSED
tests/test_nowcasting_baseline.py::test_missing_velocity_holds_position_low_confidence PASSED
tests/test_nowcasting_baseline.py::test_missing_direction_holds_position_low_confidence PASSED
tests/test_nowcasting_baseline.py::test_intensity_extrapolates_from_history PASSED
tests/test_nowcasting_baseline.py::test_intensity_fallback_without_history PASSED
tests/test_nowcasting_baseline.py::test_confidence_decreases_with_horizon PASSED
tests/test_nowcasting_baseline.py::test_stale_radar_reduces_confidence PASSED
tests/test_nowcasting_baseline.py::test_short_history_reduces_confidence PASSED
tests/test_nowcasting_baseline.py::test_lost_cells_omitted PASSED
tests/test_nowcasting_baseline.py::test_no_cells_returns_empty PASSED
11 passed in 0.27s
```

### Full suite (regression)

```text
$ cd backend; python -m pytest -q
52 passed in 3.35s
```

(41 existing + 11 new.)

## Deliverables Checklist

- [x] `NowcastingModel` protocol in `nowcasting_models.py`
- [x] `BaselineExtrapolationModel` with `name`/`version` properties
- [x] Algorithm matches brief (eligible states, projection, hold-on-missing, intensity, probability, confidence factors)
- [x] Tests: `test_nowcasting_baseline.py` (11 named cases)
- [x] Did not create engine/service/API/frontend
- [x] Commit on feature branch

## Commit

| SHA | Subject |
|-----|---------|
| `31a32a8` | feat(nowcast): add baseline extrapolation model |

Commit via `git.exe -F` workaround (per machine constraint).

## Self-Review

### Correctness

- 60 km/h east × 5 min → ~5 km; haversine assertion ±500 m passed.
- Missing speed or missing bearing holds geometry and forces confidence ≤ 0.35 (cap required when `motion.confidence=1.0`, since ×0.5 alone can stay above 0.35 at +5 min).
- Intensity 40/50/60 over 10-minute steps → slope 1.0 / min → +5=65, +60=120, locked by tests.
- Empty history keeps current mean 80 and probability `80/255`.
- Stale radar (`age > 900`) multiplies confidence by 0.6; short history (`len < 2`) by 0.75.
- `LOST`/`EXPIRED` omitted; `NEW` included; empty input → `[]`.
- Bounds translated by centroid Δlat/Δlng when projecting.

### Scope

- Did not modify Stage 1–4 paths.
- Did not add `NowcastingEngine`, service, API router, or frontend.

### Concerns (non-blocking)

- No named test locks the `frames_used < nowcast_min_frames_for_full_confidence` ×0.7 factor (implemented, not asserted).
- Intensity trend requires parseable ISO timestamps; unparseable/missing timestamps drop those samples and may fall back to current mean.
- Confidence ≤ 0.35 cap is applied after all multipliers (including stale ×0.6), so missing-motion + stale can go below 0.35.

## Files

| Path | Action |
|------|--------|
| `backend/app/engine/nowcasting_models.py` | created |
| `backend/tests/test_nowcasting_baseline.py` | created |

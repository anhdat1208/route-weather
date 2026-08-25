# Task 1 Report: Geo helper + config + schemas

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE

## Summary

Implemented Stage 5 nowcasting foundation: spherical `destination_point` geo helper, nowcast settings in `Settings`, and Pydantic schemas for predict request/response. No model, API route, or frontend changes (out of scope).

## TDD Evidence

### RED — Step 1–2: Failing test first

Created `backend/tests/test_geo_math_destination.py` with two tests (north 1 km, east 2 km + zero distance).

```text
$ cd backend; python -m pytest tests/test_geo_math_destination.py -v

ERROR collecting tests/test_geo_math_destination.py
ImportError: cannot import name 'destination_point' from 'app.engine.geo_math'
```

Failure reason matches expectation: `destination_point` not yet implemented.

### GREEN — Step 3–4: Minimal implementation

Added:

| File | Change |
|------|--------|
| `backend/app/engine/geo_math.py` | `destination_point(origin, distance_km, bearing_degrees) -> LatLng` |
| `backend/app/config.py` | Five nowcast settings with baseline/0.1 defaults |
| `backend/app/schemas/nowcasting.py` | Request/response and cell prediction schemas |

```text
$ cd backend; python -m pytest tests/test_geo_math_destination.py -v

tests/test_geo_math_destination.py::test_destination_point_north_1km PASSED
tests/test_geo_math_destination.py::test_destination_point_east_and_zero PASSED
2 passed in 0.21s
```

### Full suite (regression)

```text
$ cd backend; python -m pytest -q
41 passed in 3.76s
```

## Deliverables Checklist

- [x] `destination_point` in `geo_math.py` (verbatim from plan)
- [x] Settings: `nowcast_model_name=baseline`, `nowcast_model_version=0.1`, `nowcast_horizons_minutes=[5,10,15,30,60]`, `nowcast_intensity_max=255.0`, `nowcast_min_frames_for_full_confidence=3`
- [x] Schemas: `NowcastPredictRequest`, `NowcastModelInfo`, `PredictedCellMotion`, `PredictedRainCell`, `NowcastPredictionResponse`
- [x] Tests: `test_geo_math_destination.py` (2 cases)
- [x] Commit on feature branch

## Commit

| SHA | Subject |
|-----|---------|
| `d9656e5` | feat(nowcast): add geo destination helper and nowcasting schemas |

Commit via `git.exe -F` workaround (per machine constraint).

## Self-Review

### Correctness

- `destination_point` uses standard spherical forward geodesic formulas with `EARTH_RADIUS_M` already defined in module; zero/negative distance returns origin unchanged.
- North test: haversine back-distance ~1000 m (±15 m tolerance), lat increases, lng unchanged.
- East test: lng increases; zero distance preserves lat/lng.
- Config defaults align with planned model identity `baseline/0.1` and horizons `[5,10,15,30,60]`.
- Schemas reuse existing `LatLng` and `CellBoundsOut`; field constraints match design spec.

### Scope

- Did not modify Stage 1–4 code paths.
- Did not add API routes, baseline model, or frontend (later tasks).

### Risks / Notes

- `nowcasting.py` schemas are not yet imported by routers or tests beyond geo tests; validation will be exercised in later tasks.
- `destination_point` placed before `haversine_distance_m` in file (functional; no behavioral impact).

## Concerns

None blocking. Schemas untested directly in this task (per plan — geo helper was the TDD target; schemas are declarative Pydantic models).

## Files Touched

```
backend/app/engine/geo_math.py          (+ destination_point)
backend/app/config.py                   (+ 5 nowcast settings)
backend/app/schemas/nowcasting.py       (new)
backend/tests/test_geo_math_destination.py (new)
```

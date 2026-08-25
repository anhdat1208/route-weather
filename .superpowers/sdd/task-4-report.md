# Task 4 Report: Service + API + main registration

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE

## Summary

Exposed Stage 5 nowcasting over HTTP: `NowcastingService.predict_for_route` awaits Stage 3 `RainCellService.track_for_route` then `run_nowcast(track)`. Router `POST /api/nowcasting/predict` is registered in `main.py` inside an isolated try/except so a nowcast import failure cannot take down radar/route APIs. No frontend (out of scope).

## TDD Evidence

### RED — Step 1–2: Failing tests first

Created `backend/tests/test_nowcasting_api.py` (HTTP mock + service wiring). Production service/API did not exist yet.

```text
$ cd backend; python -m pytest tests/test_nowcasting_api.py -v

ERROR collecting tests/test_nowcasting_api.py
ImportError while importing test module '.../tests/test_nowcasting_api.py'.
tests\test_nowcasting_api.py:18: in <module>
    from app.services.nowcasting_service import NowcastingService
E   ModuleNotFoundError: No module named 'app.services.nowcasting_service'
============================== 1 error in 0.86s ===============================
```

Failure reason matches expectation: `nowcasting_service` not yet implemented.

### GREEN — Step 3–4: Minimal implementation

Added:

- `backend/app/services/nowcasting_service.py` — `NowcastingService.predict_for_route` + `get_nowcasting_service()` singleton
- `backend/app/api/nowcasting.py` — `POST /api/nowcasting/predict`
- `backend/app/main.py` — isolated nowcasting router include after rain-cells

```text
$ cd backend; python -m pytest tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py -v

tests/test_nowcasting_baseline.py ... 11 passed
tests/test_nowcasting_engine.py ... 6 passed
tests/test_nowcasting_api.py::test_nowcasting_predict_endpoint_with_mock_service PASSED
tests/test_nowcasting_api.py::test_predict_for_route_calls_track_then_engine PASSED
============================= 19 passed in 1.28s ==============================
```

### Full suite (regression)

```text
$ cd backend; python -m pytest -q
60 passed in 5.23s
```

(58 existing + 2 new.)

## Deliverables Checklist

- [x] `NowcastingService.predict_for_route(geometry, buffer_km=None) -> NowcastPredictionResponse`
- [x] Internally: `track = await get_rain_cell_service().track_for_route(...)` then `return run_nowcast(track)`
- [x] `get_nowcasting_service()` singleton like rain cells
- [x] `POST /api/nowcasting/predict` with `response_model=NowcastPredictionResponse`
- [x] Isolated try/except registration in `main.py` (after rain-cells)
- [x] Tests: `test_nowcasting_api.py` (mocked HTTP + track-then-engine unit)
- [x] Did not add frontend
- [x] Commit on feature branch

## Commit

| SHA | Subject |
|-----|---------|
| `0f4bf31` | feat(nowcast): expose POST /api/nowcasting/predict |

Commit via `git.exe -F` workaround (per machine constraint).

## Self-Review

### Correctness

- HTTP test patches `_nowcasting_service` and asserts 200, `model.name == "baseline"`, horizons `[5,10,15,30,60]`, `predictions[0].kind == "predicted"`.
- Service unit test mocks `get_rain_cell_service`; real `run_nowcast` on empty ok track → `status="ok"`, empty predictions, Vietnamese empty message, `frames_used=3`.
- `buffer_km` is forwarded as a keyword to `track_for_route`.
- Nowcasting include is a sibling try/except of rain-cells: failure logs and does not unwind the outer boot block.

### Scope

- Did not modify Stage 1–4 engines/trackers.
- Did not add frontend types, composable, or map layers.

### Concerns (non-blocking)

- HTTP test does not assert the mock was called with `geometry` / `buffer_km` (same pattern as rain-cells API test).
- No dedicated HTTP test for request validation (`geometry` min_length=2) or `unavailable` passthrough via the live service.
- `radar_age_seconds` remains `None` (Stage 5 engine default); service does not derive radar age.

## Files

| Path | Action |
|------|--------|
| `backend/app/services/nowcasting_service.py` | created |
| `backend/app/api/nowcasting.py` | created |
| `backend/app/main.py` | modified |
| `backend/tests/test_nowcasting_api.py` | created |

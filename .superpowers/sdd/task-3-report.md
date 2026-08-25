# Task 3 Report: NowcastingEngine

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE

## Summary

Implemented `run_nowcast`: takes a Stage 3 `RainCellTrackResponse`, runs the active `NowcastingModel` (default `BaselineExtrapolationModel`), and returns a normalized `NowcastPredictionResponse` with status, model identity, horizons, and Vietnamese messages. No service, API, or frontend (out of scope).

## TDD Evidence

### RED — Step 1–2: Failing tests first

Created `backend/tests/test_nowcasting_engine.py` with the four named cases from the brief plus two status-rule cases (unavailable default message; missing-motion → partial). Production module did not exist yet.

```text
$ cd backend; python -m pytest tests/test_nowcasting_engine.py -v

ImportError while importing test module '.../tests/test_nowcasting_engine.py'.
tests\test_nowcasting_engine.py:6: in <module>
    from app.engine.nowcasting_engine import run_nowcast
E   ModuleNotFoundError: No module named 'app.engine.nowcasting_engine'
============================== 1 error in 0.48s ===============================
```

Failure reason matches expectation: `nowcasting_engine` not yet implemented.

### GREEN — Step 3–4: Minimal implementation

Added `backend/app/engine/nowcasting_engine.py`:

- `run_nowcast(track, *, model=None, generated_at=None, radar_age_seconds=None)`
- Default model `BaselineExtrapolationModel()`; injected `NowcastingModel` supported
- `horizons` from `settings.nowcast_horizons_minutes`; `model` info from `name`/`version`; `frames_used` from track
- `radar_age_seconds` optional kwarg, default `None`, forwarded to `predict` and the response
- Status: `unavailable` passthrough (no predict, keep track message or Vietnamese default) → track `partial` → any prediction with `confidence < 0.35` **and** missing speed/bearing → empty predictions with track ok → else `ok`

```text
$ cd backend; python -m pytest tests/test_nowcasting_engine.py -v

tests/test_nowcasting_engine.py::test_engine_unavailable_passthrough PASSED
tests/test_nowcasting_engine.py::test_engine_unavailable_uses_vietnamese_default PASSED
tests/test_nowcasting_engine.py::test_engine_empty_cells_ok_with_message PASSED
tests/test_nowcasting_engine.py::test_engine_runs_baseline_and_sets_model_info PASSED
tests/test_nowcasting_engine.py::test_engine_partial_when_track_partial PASSED
tests/test_nowcasting_engine.py::test_engine_partial_when_missing_motion PASSED
6 passed in 0.31s
```

### Full suite (regression)

```text
$ cd backend; python -m pytest -q
58 passed in 3.94s
```

(52 existing after Task 2 + 6 new.)

## Deliverables Checklist

- [x] `run_nowcast` in `nowcasting_engine.py`
- [x] Consumes `RainCellTrackResponse` + `BaselineExtrapolationModel` / injected `NowcastingModel`
- [x] Produces `NowcastPredictionResponse`
- [x] Status rules: unavailable / track partial / missing-motion partial / empty ok / ok
- [x] Model info, horizons, frames_used, optional `radar_age_seconds`
- [x] Tests: `test_nowcasting_engine.py` (4 named + 2 status-rule cases)
- [x] Did not create service/API/frontend
- [x] Commit on feature branch

## Commit

| SHA | Subject |
|-----|---------|
| `0ec15b3` | feat(nowcast): add nowcasting engine orchestrator |

Commit via `git.exe -F` workaround (per machine constraint).

## Self-Review

### Correctness

- Unavailable with cells still returns `predictions=[]` and does not call the model.
- Unavailable without track message uses Vietnamese default.
- Track `ok` + empty cells → `ok`, `predictions=[]`, Vietnamese empty message.
- Track `ok` + TRACKING cell with motion → 5 predicted horizons, `model=baseline/0.1`, `status=ok`.
- Track `partial` keeps `partial` even when predictions exist; preserves track message.
- Missing speed on an otherwise ok track → `partial` + incomplete-motion Vietnamese message (baseline +60 min confidence drops below 0.35).

### Scope

- Did not modify Stage 1–4 paths.
- Did not add `NowcastingService`, API router, or frontend.

### Concerns (non-blocking)

- `NowcastingModel` protocol only declares `predict`; engine reads `name`/`version` by duck typing (Baseline already exposes them). An injected stub without those attributes would raise `AttributeError`.
- Incomplete-motion gate uses `confidence < 0.35` (brief verbatim), not `<= 0.35`. Baseline clamps missing-motion confidence **to** 0.35 at short horizons; default horizons include 60 min so the gate still fires. A caller injecting `horizons=[5]` via settings-only path is not possible here (engine always uses settings list).

## Files

| Path | Action |
|------|--------|
| `backend/app/engine/nowcasting_engine.py` | created |
| `backend/tests/test_nowcasting_engine.py` | created |

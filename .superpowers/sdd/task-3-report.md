# Task 3 Report: BaselineTrafficModel

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `bf9df6c` — `feat(traffic): add baseline traffic prediction model`  
**Date:** 2026-08-25

## Scope

Implemented Task 3 only per brief:
- Extracted `tod_factor` + `hour_weekday` / `tod_factor_at` into `backend/app/engine/traffic_tod.py`
- Updated `SyntheticTrafficProvider` to import `tod_factor` from `traffic_tod`
- `TrafficPredictionModel` Protocol + `BaselineTrafficModel` in `backend/app/engine/traffic_models.py`
- Tests in `backend/tests/test_traffic_baseline.py` (verbatim from brief)

No weather impact, engine combine, API, or frontend were added.

## TDD Evidence

### RED — Step 2 (failing tests first)

Created `backend/tests/test_traffic_baseline.py` with two test functions verbatim from the brief, then ran:

```
cd backend; python -m pytest tests/test_traffic_baseline.py -v
```

Output:

```
ModuleNotFoundError: No module named 'app.engine.traffic_models'
```

Result: **FAIL** as expected (module missing).

### GREEN — Step 4 (implementation)

Implemented:
1. `traffic_tod.py` — locked `tod_factor(hour, weekday)`, `hour_weekday(at)`, `tod_factor_at(at)`
2. `traffic_models.py` — `TrafficPredictionModel` Protocol + `BaselineTrafficModel` with locked 40% ToD drift algorithm
3. Refactored `synthetic_traffic.py` to import `tod_factor` from `traffic_tod`

Re-ran:

```
cd backend; python -m pytest tests/test_traffic_baseline.py tests/test_traffic_synthetic.py tests/test_traffic_state.py -v
```

Output:

```
8 passed in 0.28s
```

Result: **PASS** — all 8 tests green (2 baseline + 3 synthetic + 3 state).

## Files Changed

| File | Action |
|------|--------|
| `backend/app/engine/traffic_tod.py` | Created — shared ToD helpers |
| `backend/app/engine/traffic_models.py` | Created — Protocol + BaselineTrafficModel |
| `backend/app/providers/synthetic_traffic.py` | Modified — import `tod_factor` from `traffic_tod` |
| `backend/tests/test_traffic_baseline.py` | Created — unit tests |

## Interfaces Delivered

### `TrafficPredictionModel` (Protocol)

```python
@property
def name(self) -> str: ...
@property
def version(self) -> str: ...
def predict_base(
    self,
    segments: Sequence[RoadSegmentOut],
    *,
    at: datetime,
    horizons: list[int],
) -> list[tuple[str, int, SpeedCongestionPair]]: ...
```

### `BaselineTrafficModel.predict_base`

Per segment × horizon (skip `traffic is None` or missing `free_flow_speed_kmh`):

1. `current = traffic.current_speed_kmh` (fallback `free_flow` if None)
2. `expected_future = clamp(free * tod_factor_at(at + h), free)`
3. `base_speed = clamp(current + 0.40 * (expected_future - current), free)`
4. `speed_delta_pct = (base_speed / current) - 1` if `current > 0` else `0`
5. `congestion` from `relative_speed` + `congestion_from_relative`

`name` / `version` from `settings.traffic_model_name` / `settings.traffic_model_version` (`baseline` / `0.1`).

## Self-Review

### Correctness

- Locked algorithm matches brief; no invented history beyond ToD drift.
- All horizons emitted per segment (`len(segs) * 4` for 4 horizons).
- Predicted speeds stay within clamp band `[0.20 * free, 1.05 * free]`.
- Synthetic provider behavior unchanged after `tod_factor` extraction (3 synthetic tests still pass).

### Conventions

- Follows `nowcasting_models.py` pattern (Protocol + settings-backed name/version).
- Shared ToD logic in `engine/` avoids circular imports between provider and model.

### Concerns / Follow-ups

- **`expected_now` unused:** Brief lists it for documentation; drift uses `current` (observed) → `expected_future` only.
- **`missing_current` flag:** Not surfaced in `SpeedCongestionPair`; fallback to `free_flow` is internal only — Task 5 engine may need confidence handling.
- **Timezone:** Same as Task 2 — `tod_factor_at` uses datetime's own tz; tests use UTC.

## Verification Commands

```powershell
cd backend
python -m pytest tests/test_traffic_baseline.py tests/test_traffic_synthetic.py tests/test_traffic_state.py -v
```

# Task 2 Report: TrafficProvider + SyntheticTrafficProvider

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `02dfab8` — `feat(traffic): add synthetic traffic provider`  
**Date:** 2026-08-25

## Scope

Implemented Task 2 only per brief:
- `TrafficProvider` Protocol in `backend/app/providers/base.py`
- `SyntheticTrafficProvider` in `backend/app/providers/synthetic_traffic.py`
- Tests in `backend/tests/test_traffic_synthetic.py`

No BaselineTrafficModel, weather impact, engine, API, or frontend were added.

## TDD Evidence

### RED — Step 2 (failing tests first)

Created `backend/tests/test_traffic_synthetic.py` with three test functions verbatim from the brief, then ran:

```
cd backend; python -m pytest tests/test_traffic_synthetic.py -v
```

Output:

```
ModuleNotFoundError: No module named 'app.providers.synthetic_traffic'
```

Result: **FAIL** as expected (module missing).

### GREEN — Step 4 (implementation)

Implemented:
1. `TrafficProvider` Protocol in `backend/app/providers/base.py`
2. `SyntheticTrafficProvider` with locked `tod_factor` formula and segment builder
3. Uses `sample_points_by_distance` with traffic sample settings from config
4. Fills `TrafficStateOut` via `relative_speed`, `congestion_from_relative`, `clamp_speed`

Re-ran:

```
cd backend; python -m pytest tests/test_traffic_synthetic.py tests/test_traffic_state.py -v
```

Output:

```
6 passed in 0.60s
```

Result: **PASS** — all 6 tests green (3 synthetic + 3 state from Task 1).

## Files Changed

| File | Action |
|------|--------|
| `backend/app/providers/base.py` | Modified — added `TrafficProvider` Protocol |
| `backend/app/providers/synthetic_traffic.py` | Created — `tod_factor` + `SyntheticTrafficProvider` |
| `backend/tests/test_traffic_synthetic.py` | Created — unit tests |

## Interfaces Delivered

### `TrafficProvider` (Protocol)

```python
def current_for_route(
    self,
    geometry: list[LatLng],
    *,
    at: datetime | None = None,
) -> list[RoadSegmentOut]: ...
```

### `SyntheticTrafficProvider.current_for_route`

- Samples route via `sample_points_by_distance` with `traffic_sample_*` settings
- Builds N-1 segments from N sample points
- Segment id: `route-seg-{i}`, geometry: `[samples[i].point, samples[i+1].point]`
- `road_type="unknown"`, `source="synthetic"`, `stale=False`
- `free_flow_speed_kmh` from `settings.traffic_free_flow_default_kmh` (40.0)
- Current speed: `clamp(free_flow * tod_factor * (1 - 0.04 * (index % 5)), free_flow)`

### Locked `tod_factor(hour, weekday)`

| Condition | Factor |
|-----------|--------|
| Weekday (0–4), hour in {7,8} or {17,18} | 0.70 |
| Weekday, hour in {6,9,16,19} | 0.82 |
| Weekday, else | 0.95 |
| Weekend, hour in {10,11,12,17,18} | 0.88 |
| Weekend, else | 0.98 |

## Self-Review

### Correctness

- ToD formula matches brief exactly; rush-hour (08:00 Tue) slower than night (02:00) verified by test.
- Deterministic output for same timestamp confirmed.
- Segment labeling (`id`, `source`, `stale`, `geometry` length) matches spec.
- `clamp_speed` applied before `relative_speed` / `congestion_from_relative` as required.

### Conventions

- Follows existing provider patterns (`from __future__ import annotations`, settings import, schema types).
- `tod_factor` kept inline in `synthetic_traffic.py` per brief (Task 3 will extract to `traffic_tod.py`).

### Concerns / Follow-ups

- **Timezone:** `tod_factor` uses `at.hour` and `at.weekday()` in the datetime's own timezone; callers should pass UTC or local consistently. Tests use UTC.
- **Short routes:** With `traffic_sample_min_points=3`, a 2-point geometry yields 2 segments minimum — test passes with `len(segs) >= 1`.
- **No dedicated `tod_factor` unit tests** in this task — covered indirectly via rush/night and determinism tests; Task 3 may add explicit ToD tests when extracting.

## Verification Commands

```powershell
cd backend
python -m pytest tests/test_traffic_synthetic.py tests/test_traffic_state.py -v
```

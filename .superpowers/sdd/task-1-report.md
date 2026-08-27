# Task 1 Report: Config, schemas, congestion helpers

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `cb5881a` — `feat(traffic): add schemas and congestion helpers`  
**Date:** 2026-08-25

## Scope

Implemented Task 1 only per brief:
- Settings fields for traffic prediction in `backend/app/config.py`
- Pydantic schemas in `backend/app/schemas/traffic.py`
- Congestion helpers in `backend/app/engine/traffic_state.py`
- Tests in `backend/tests/test_traffic_state.py`

No providers, engines, API, or frontend were added.

## TDD Evidence

### RED — Step 2 (failing tests first)

Created `backend/tests/test_traffic_state.py` with three test functions verbatim from the brief, then ran:

```
cd backend; python -m pytest tests/test_traffic_state.py -v
```

Output:

```
ERROR collecting tests/test_traffic_state.py
ImportError while importing test module ...
tests\test_traffic_state.py:3: in <module>
    from app.engine.traffic_state import (
E   ModuleNotFoundError: No module named 'app.engine.traffic_state'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

Result: **FAIL** as expected (module missing).

### GREEN — Step 4 (implementation)

Implemented:
1. `backend/app/engine/traffic_state.py` — `relative_speed`, `congestion_from_relative`, `clamp_speed`
2. `backend/app/schemas/traffic.py` — all schemas from brief
3. `backend/app/config.py` — 10 traffic settings fields appended before `# Server`

Re-ran:

```
cd backend; python -m pytest tests/test_traffic_state.py -v
```

Output:

```
tests/test_traffic_state.py::test_relative_speed_and_none PASSED         [ 33%]
tests/test_traffic_state.py::test_congestion_bands PASSED                [ 66%]
tests/test_traffic_state.py::test_clamp_speed_band PASSED                [100%]

============================== 3 passed in 0.04s ==============================
```

Result: **PASS** — all 3 tests green.

## Files Changed

| File | Action |
|------|--------|
| `backend/app/config.py` | Modified — added 10 traffic settings |
| `backend/app/engine/traffic_state.py` | Created — congestion helpers |
| `backend/app/schemas/traffic.py` | Created — request/response schemas |
| `backend/tests/test_traffic_state.py` | Created — unit tests |

## Interfaces Delivered

### Settings (`Settings` in `config.py`)

- `traffic_model_name: str = "baseline"`
- `traffic_model_version: str = "0.1"`
- `traffic_horizons_minutes: list[int] = [5, 10, 15, 30]`
- `traffic_sample_interval_km: float = 5.0`
- `traffic_sample_min_points: int = 3`
- `traffic_sample_max_points: int = 24`
- `traffic_free_flow_default_kmh: float = 40.0`
- `traffic_stale_after_seconds: int = 900`
- `traffic_rain_nearby_km: float = 8.0`
- `traffic_base_confidence: float = 0.75`

### Helpers (`traffic_state.py`)

- `relative_speed(current, free_flow) -> float | None`
- `congestion_from_relative(relative) -> CongestionLevel | None`
- `clamp_speed(speed, free_flow) -> float`

### Schemas (`traffic.py`)

- `TrafficPredictRequest`
- `TrafficModelInfo`
- `TrafficStateOut`
- `RoadSegmentOut`
- `SpeedCongestionPair`
- `WeatherImpactInfo`
- `TrafficPredictionOut`
- `TrafficPredictionResponse`

Plus type aliases: `TrafficStatus`, `NowcastEmbedStatus`, `CongestionLevel`, `WeatherImpactLevel`, `RoadType`.

## Self-Review

### Correctness

- Congestion bands match brief thresholds (`_FREE=0.85`, `_SLOW=0.70`, `_MODERATE=0.50`, `_HEAVY=0.30`).
- `clamp_speed` enforces `[0.20, 1.05] * free_flow` when `free_flow > 0`; passthrough with `max(0, speed)` when invalid/missing free flow.
- `relative_speed` returns `None` for missing inputs or `free_flow <= 0`.
- Schemas match brief field names, types, and validators exactly.

### Conventions

- Follows existing patterns: `from __future__ import annotations`, Pydantic `BaseModel` + `Field`, settings grouped with related nowcast fields.
- `LatLng` imported from `app.schemas.common` as in other schema modules.

### Scope discipline

- No overbuilding: no provider stubs, engine wiring, API routes, or schema re-exports in `__init__.py`.
- `RoadType` literal defined but `RoadSegmentOut.road_type` remains `str | None` per brief.

### Minor notes (non-blocking)

- `RoadType` alias is unused until later tasks wire road classification — intentional per spec.
- No dedicated schema validation tests; brief only required congestion helper tests.

## Status

**DONE** — TDD cycle complete, tests pass, commit created.

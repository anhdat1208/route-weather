# Task 4 Report: WeatherImpactModel

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `3c4d1ed` — `feat(traffic): add rule-based weather impact model`  
**Date:** 2026-08-25

## Scope

Implemented Task 4 only per brief:
- `backend/app/engine/weather_impact.py` — `estimate_impact(segment, *, horizon, nowcast) -> WeatherImpactInfo`
- Locked algorithm: intensity bands (<40 / <90 / else), deltas (−7% / −15% / −25%), rain_probability × confidence scaling, heavy/severe dampening (×0.5), reason codes
- Tests in `backend/tests/test_weather_impact.py` (14 cases)

No traffic_engine combine, API, or frontend were added.

## TDD Evidence

### RED — Step 2 (failing tests first)

Created `backend/tests/test_weather_impact.py`, then ran:

```
cd backend; python -m pytest tests/test_weather_impact.py -v
```

Output:

```
ModuleNotFoundError: No module named 'app.engine.weather_impact'
```

Result: **FAIL** as expected (module missing).

### GREEN — Step 4 (implementation)

Implemented `estimate_impact` consuming `RoadSegmentOut`, `NowcastPredictionResponse`, `min_distance_to_polyline_m`, `settings.traffic_rain_nearby_km`.

Re-ran:

```
cd backend; python -m pytest tests/test_weather_impact.py tests/test_traffic_state.py tests/test_traffic_synthetic.py tests/test_traffic_baseline.py -v
```

Output:

```
22 passed in 0.35s
```

Result: **PASS** — 14 new + 8 existing traffic tests green.

## Files Changed

| File | Action |
|------|--------|
| `backend/app/engine/weather_impact.py` | Created — rule-based weather impact |
| `backend/tests/test_weather_impact.py` | Created — 14 unit tests |

## Interfaces Delivered

```python
def estimate_impact(
    segment: RoadSegmentOut,
    *,
    horizon: int,
    nowcast: NowcastPredictionResponse | None,
) -> WeatherImpactInfo: ...
```

Early exits: `nowcast is None` → `no_rain_prediction`; `status == unavailable` → `nowcast_unavailable`; empty predictions → `no_rain_prediction`; no nearby cells → `no_rain_nearby`.

## Test Coverage

| Scenario | Asserted |
|----------|----------|
| No rain nearby | delta 0, `no_rain_nearby` |
| Empty predictions | `no_rain_prediction` |
| Unavailable nowcast | `nowcast_unavailable` |
| None nowcast | `no_rain_prediction` |
| Light / moderate / heavy bands | level + delta + reason |
| None intensity | treated as low (−7%) |
| Already congested (heavy/severe) | delta × 0.5 + reason |
| Low confidence (<0.4) | scaled delta + reason |
| Rain probability scaling | delta × probability |
| Max intensity pick | highest cell wins |
| Horizon filter | wrong horizon → no nearby |

## Self-Review

### Correctness

- Distance check uses `traffic_rain_nearby_km * 1000` meters via `min_distance_to_polyline_m`.
- None intensity → low band per spec (not skipped).
- Reasons order: dampening/low-confidence codes before rain-level reason.

### Scope

- Did not implement `traffic_engine` combine, confidence, or API.
- Did not modify schemas (Task 1 already delivered `WeatherImpactInfo`).

### Concerns (non-blocking)

- Segment geometry with `<2` points silently yields no nearby cells (no explicit error).
- No test for `nowcast.status == "partial"` with valid predictions (should work same as ok).
- Polyline distance uses sampled segments (same as fusion engine); edge precision not calibrated.

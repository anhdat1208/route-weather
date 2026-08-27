# Task 5 Report: TrafficPredictionEngine

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `1f4703e` — `feat(traffic): add traffic prediction engine`  
**Date:** 2026-08-25

## Scope

Implemented Task 5 per plan (`docs/superpowers/plans/2026-08-25-stage6-traffic-prediction.md`):
- `backend/app/engine/traffic_engine.py` — `run_traffic_prediction(segments, *, nowcast, at) -> TrafficPredictionResponse`
- Locked combine: `clamp(base × (1 + impact_delta), free_flow)`; weather_adjusted delta from current
- Locked confidence: base 0.75, ×0.7 stale, ×0.5 missing current, horizon decay, ×0.75 bad nowcast + non-none impact, ×0.85 low_nowcast_confidence, ×0.9 no_history
- Status table with Vietnamese messages
- Tests in `backend/tests/test_traffic_engine.py` (7 cases)

No TrafficService, API, or frontend (Task 6).

## TDD Evidence

### RED — Step 2

```
cd backend; python -m pytest tests/test_traffic_engine.py -v
```

```
ModuleNotFoundError: No module named 'app.engine.traffic_engine'
```

### GREEN — Step 4

```
cd backend; python -m pytest tests/test_traffic_engine.py tests/test_weather_impact.py tests/test_traffic_baseline.py -v
```

```
23 passed in 0.44s
```

## Files Changed

| File | Action |
|------|--------|
| `backend/app/engine/traffic_engine.py` | Created — combine, confidence, status |
| `backend/tests/test_traffic_engine.py` | Created — 7 unit tests |

## Interfaces Delivered

```python
def run_traffic_prediction(
    segments: Sequence[RoadSegmentOut],
    *,
    nowcast: NowcastPredictionResponse | None,
    at: datetime,
) -> TrafficPredictionResponse: ...
```

Uses `BaselineTrafficModel().predict_base`, `estimate_impact`, `settings.traffic_horizons_minutes`, model info from settings.

## Test Coverage

| Scenario | Asserted |
|----------|----------|
| Combine 28 + (−20%) | adjusted 22.4 |
| Confidence horizon | 30m < 5m |
| Stale traffic | lowers confidence |
| Empty segments | unavailable, skipped, Vietnamese message |
| Nowcast unavailable | ok, base predictions, impact 0, message |
| Heavy rain | adjusted < base |
| Missing current speed | partial status, adj delta None |

## Self-Review

### Correctness

- Combine and confidence formulas match locked spec exactly.
- Nowcast unavailable still emits base predictions with zero weather impact.
- Status priority: unavailable → partial (missing current) → nowcast-unavailable message → ok.

### Scope

- Did not implement TrafficService, API router, or frontend.
- Did not modify schemas or prior modules.

### Concerns (non-blocking)

- `missing_current` surfaced at response level but baseline still substitutes free-flow (documented in Task 3 minors).
- No test for nowcast `partial` status with non-none impact (confidence ×0.75 path untested directly).
- Combined status when both partial + nowcast unavailable: partial wins (message for missing current only).

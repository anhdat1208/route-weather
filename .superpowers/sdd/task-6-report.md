# Task 6 Report: TrafficService + API

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `cafbe3f` — `feat(traffic): expose POST /api/traffic/prediction`  
**Date:** 2026-08-25  
**Status:** DONE

## Scope

Implemented Task 6 per plan (`docs/superpowers/plans/2026-08-25-stage6-traffic-prediction.md`):
- `backend/app/services/traffic_service.py` — `TrafficService.predict_for_route`, `get_traffic_service()` singleton
- `backend/app/api/traffic.py` — `POST /api/traffic/prediction`
- `backend/app/main.py` — isolated try/except router include
- `backend/tests/test_traffic_api.py` — API mock + nowcast failure resilience

No frontend (Tasks 7–10).

## TDD Evidence

### RED — Step 2

```
cd backend; python -m pytest tests/test_traffic_api.py -v
```

```
ModuleNotFoundError: No module named 'app.services.traffic_service'
```

### GREEN — Step 4

```
cd backend; python -m pytest tests/test_traffic_api.py tests/test_traffic_engine.py tests/test_nowcasting_api.py -v
```

```
11 passed in 0.96s
```

## Files Changed

| File | Action |
|------|--------|
| `backend/app/services/traffic_service.py` | Created — synthetic segments → nowcast → engine |
| `backend/app/api/traffic.py` | Created — POST endpoint |
| `backend/app/main.py` | Modified — traffic router with isolated try/except |
| `backend/tests/test_traffic_api.py` | Created — 2 tests |

## Interfaces Delivered

```python
class TrafficService:
    async def predict_for_route(
        self, geometry: list[LatLng], buffer_km: float | None = None
    ) -> TrafficPredictionResponse: ...

def get_traffic_service() -> TrafficService: ...
```

Flow: `SyntheticTrafficProvider().current_for_route` → try `get_nowcasting_service().predict_for_route` (exception → unavailable nowcast with empty predictions) → `run_traffic_prediction`.

## Test Coverage

| Scenario | Asserted |
|----------|----------|
| API with mocked service | 200, model/horizons/predictions |
| Nowcast raises at service level | status ok, nowcast_status unavailable, zero weather impact, Vietnamese message |

## Self-Review

### Correctness

- Nowcast exceptions do not fail the traffic request; engine receives unavailable nowcast.
- Router registration mirrors nowcasting isolated try/except pattern.
- Singleton pattern matches `get_nowcasting_service()`.

### Scope

- Backend only; no frontend changes.

### Concerns (non-blocking)

- Broad `except Exception` on nowcast — intentional per spec; any nowcast outage degrades gracefully.
- Service test hits real synthetic provider + engine (not fully mocked); acceptable integration coverage.

## Commit

| SHA | Subject |
|-----|---------|
| `cafbe3f` | feat(traffic): expose POST /api/traffic/prediction |

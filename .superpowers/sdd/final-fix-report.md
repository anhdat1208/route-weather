# Stage 6 Final Fix Report

**Date:** 2026-08-25  
**Branch:** `feat/stage6-traffic-prediction`

## Status

**PASS** — All must-fix and should-fix items addressed in one pass.

## Fixes Applied

### 1. Map empty at NOW with prediction-only toggle (Important)

**File:** `frontend/app/components/RouteMap.vue`

Updated `visibleTrafficMode()`:
- `trafficPredictionEnabled && horizon === 0` → `"current"` (even if `trafficEnabled` is false)
- Predicted mode only when `trafficPredictionEnabled && horizon > 0`
- Current mode when `trafficEnabled` as before

### 2. README scope bullets (Should fix)

**File:** `README.md`

Removed `traffic prediction` from Stage 1–3 "Không có / Chưa có" bullets so early scope no longer contradicts Stage 6 completion.

### 3. Log nowcast failures (Should fix)

**File:** `backend/app/services/traffic_service.py`

Added `logger.exception(...)` in the nowcast fallback `except` block; fallback behavior unchanged.

## Commits

| Hash | Message |
|------|---------|
| `030c743` | fix(traffic): show current traffic at NOW when prediction enabled |
| `9467108` | docs: align README scope with Stage 6 traffic |

## Verification

| Check | Result |
|-------|--------|
| `cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit` | PASS (exit 0) |
| `cd backend; python -m pytest tests/test_traffic_api.py tests/test_traffic_engine.py -v` | PASS — 9/9 |

## Deferred (unchanged)

- CongestionLevel duplication
- Thin tests
- UTC ToD
- Partial FE message
- HTML escape

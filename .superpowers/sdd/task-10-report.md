# Task 10 Report: Wire index.vue + README + regression tests

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `ad0eff8` — `feat(traffic): wire Stage 6 UI and document baseline traffic prediction`  
**Date:** 2026-08-25  
**Status:** DONE

## Scope

Implemented Task 10 per brief (`.superpowers/sdd/task-10-brief.md`):
- Modified `frontend/app/pages/index.vue` — wire `useTraffic` to RadarControls + RouteMap
- Modified `README.md` — Stage 6 section, roadmap checkbox, API/architecture updates
- Minor fix `frontend/app/components/RadarControls.vue` — loading copy when only current traffic toggle on

### index.vue wiring

- Import `useTraffic` + `trafficModelLabel`
- Watch `[routeGeometry, trafficEnabled, trafficPredictionEnabled]` → `fetchTraffic`
- `onRefreshLayers` refreshes traffic when either toggle on
- Pass traffic props/events to `RadarControls` and `RouteMap`
- Nowcast horizon wiring unchanged

### README

- New `## Stage 6 — Traffic Prediction (baseline)` with pipeline diagram, API, synthetic disclaimer, test instructions
- Roadmap `[x] Stage 6`; link to design spec; Stage 5 section intact
- Architecture diagram + API table + known limitations updated

### RadarControls minor fix

- Loading: `Đang tải giao thông…` when only `trafficEnabled`; `Đang dự báo giao thông…` when prediction toggle on

## Verification

Backend regression (from brief):

```text
$ cd backend; python -m pytest tests/test_traffic_state.py tests/test_traffic_synthetic.py tests/test_traffic_baseline.py tests/test_weather_impact.py tests/test_traffic_engine.py tests/test_traffic_api.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v
66 passed in 1.87s
```

TypeScript:

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

No in-browser UI verification in this session.

## Deliverables Checklist

- [x] `useTraffic` imported and wired in `index.vue`
- [x] Watch routeGeometry + traffic toggles → fetchTraffic
- [x] onRefreshLayers refreshes traffic when toggles on
- [x] Props passed to RadarControls and RouteMap
- [x] Nowcast horizon wiring untouched
- [x] README Stage 6 section + roadmap + design spec link
- [x] Backend regression suite all PASS
- [x] RadarControls loading copy fix (optional)
- [x] Commit on feature branch

## Files

| Path | Action |
|------|--------|
| `frontend/app/pages/index.vue` | Modified |
| `frontend/app/components/RadarControls.vue` | Modified (loading copy) |
| `README.md` | Modified |

## Self-Review

### Correctness

- Mirrors rain-cells/nowcasting watch + refresh patterns.
- Independent traffic horizon state; does not touch nowcast `selectedHorizon`.
- RouteMap receives segments + `predictionsForHorizon` from composable.

### Concerns (non-blocking)

- No live browser test with real GraphHopper route in this session.
- `partial` traffic status does not surface as error (same as Task 7 note); segments still render.
- Stage 6 complete on branch; Stage 7 routing/intelligence still out of scope.

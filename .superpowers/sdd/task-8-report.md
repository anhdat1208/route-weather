# Task 8 Report: Wire index.vue + README

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE_WITH_CONCERNS

## Summary

Wired Stage 5 end-to-end in `index.vue`: one `useNowcasting()` call, rain-cell-style geometry watch + `onRefreshLayers`, props into `RadarControls` and `RouteMap`. Documented baseline nowcasting in `README.md` and marked roadmap Stage 5 done. Reset `nowcastClickBound` on `RouteMap` unmount (Task 7 remount harden).

## TDD Evidence

No new frontend test file (same as Tasks 5–7; no Vue test runner). Backend regression suite from the brief:

```text
$ cd backend; python -m pytest tests/test_geo_math_destination.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v
============================= 37 passed in 0.87s ==============================
```

TypeScript check after wiring:

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

No in-browser pass (no running frontend/backend in this session).

## Deliverables Checklist

- [x] Import/use `useNowcasting` once in `index.vue`
- [x] Pass nowcasting props to `RadarControls` (enabled, loading, error, model label, horizon, count)
- [x] Pass `nowcastingEnabled`, `selectedHorizon`, `predictionsForHorizon`, `response.model` to `RouteMap`
- [x] Watch route geometry / nowcasting enabled → `fetchNowcast(geom)` (same geometry as rain cells)
- [x] `onRefreshLayers` refreshes nowcast when enabled
- [x] README Stage 5: architecture one-liner, `POST /api/nowcasting/predict`, baseline ≠ trained ML, pytest + UI toggle
- [x] Roadmap Stage 5 marked `[x]`; baseline limitations noted
- [x] `RouteMap` `onBeforeUnmount` sets `nowcastClickBound = false`
- [x] Commit on feature branch

## Commit

| SHA | Subject |
|-----|---------|
| `795d72d` | feat(nowcast): wire Stage 5 UI and document baseline nowcasting |

Commit via `git.exe -F` workaround (per machine constraint). Did not include `.superpowers/sdd/*`.

## Self-Review

### Correctness

- Fetch path mirrors rain cells: enable + geometry ≥ 2, or refresh while enabled with current `routeGeometry`.
- Predicted overlay uses `predictionsForHorizon` (empty on NOW / horizon `0`); model comes from `nowcastResponse.model`.
- Observed rain-cell / radar / satellite wiring unchanged.

### Scope

- `index.vue`, `README.md`, one-line `RouteMap.vue` cleanup.

### Concerns (non-blocking)

- Status count is unique `cell_id`s across all horizons, not `predictionsForHorizon.length`, so NOW still shows a count while the map hides predicted layers.
- No browser verification of toggle → fetch → overlay → remount click handler.
- Architecture overview still omits satellite/fusion (pre-existing); Stage 5 line was added only.
- No frontend unit tests for the page wiring.

## Files

| Path | Action |
|------|--------|
| `frontend/app/pages/index.vue` | modified |
| `README.md` | modified |
| `frontend/app/components/RouteMap.vue` | modified (remount flag reset) |

# Task 6 Report: RadarControls — toggle + timeline

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE_WITH_CONCERNS

## Summary

Extended `RadarControls.vue` with a Nowcasting checkbox (same rain-cells pattern: disabled without route, status lines) and a horizon timeline (`NOW`, `+5m`, `+10m`, `+15m`, `+30m`, `+60m`) when `nowcastingEnabled && routeReady`. Selected horizon uses existing blue accent classes. Disclaimer `Dự báo baseline — không phải radar quan sát` plus optional model label.

## TDD Evidence

No frontend Jest (same as Task 5). Brief restricted edits to this Vue file only, so no new test file.

TypeScript check after implementation:

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

`npx nuxi typecheck` was not used (`vue-tsc` not installed). No browser verification in this task (controls are not wired in `index.vue` until Task 8).

## Deliverables Checklist

- [x] Props: `nowcastingEnabled`, `nowcastingLoading`, `nowcastingError`, `nowcastingModelLabel`, `selectedHorizon` (`NowcastSelectedHorizon`), `nowcastPredictionCount`; `routeReady` already existed
- [x] Emits: `update:nowcastingEnabled`, `update:selectedHorizon`
- [x] Timeline buttons only when `nowcastingEnabled && routeReady`; NOW → `0`, else `5/10/15/30/60`
- [x] Note: `Dự báo baseline — không phải radar quan sát` + model label
- [x] Toggle markup follows rain-cells (checkbox + loading/error/count)
- [x] Commit on feature branch
- [x] Did not modify other files

## Commit

| SHA | Subject |
|-----|---------|
| `7c3d646` | feat(nowcast): add nowcasting toggle and horizon timeline UI |

Commit via `git.exe -F` workaround (per machine constraint).

## Self-Review

### Correctness

- Toggle disabled when `!routeReady`; helper copy mirrors rain cells.
- Horizon list is the spec set; selected state uses `border-blue-500` / `text-blue-400` / `bg-blue-500/20`.
- `selectedHorizon` typed as `NowcastSelectedHorizon` so emit values stay `0 | 5 | 10 | 15 | 30 | 60`.

### Scope

- Only `frontend/app/components/RadarControls.vue`. `index.vue` / `RouteMap` left for Tasks 7–8.

### Concerns (non-blocking)

- New props are required (same as rain cells). Until Task 8 wires `index.vue`, Vue will warn about missing props at runtime; the toggle stays off because `nowcastingEnabled` is falsy.
- No unit tests and no in-browser pass; UI behavior is unverified until wiring.
- Duplicate “Cần có lộ trình…” lines when both rain-cells and nowcasting need a route; matches the rain-cells pattern rather than merging copy.

## Files

| Path | Action |
|------|--------|
| `frontend/app/components/RadarControls.vue` | modified |

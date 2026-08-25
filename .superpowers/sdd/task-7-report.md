# Task 7 Report: RouteMap predicted layers + inspection panel

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE_WITH_CONCERNS

## Summary

Extended `RouteMap.vue` with predicted nowcast layers (distinct from observed rain cells) and a Vietnamese click popup. GeoJSON/popup helpers live in `utils/nowcast.ts`. Did not modify `index.vue`.

Layers show only when `nowcastingEnabled && selectedHorizon > 0` and there is at least one cell whose `forecast_minutes` matches the selected horizon.

## TDD Evidence

No frontend Jest (same as Tasks 5–6). Brief asked for TypeScript sanity, not a new test file.

TypeScript check after implementation:

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

`npx nuxi typecheck` was not used (`vue-tsc` not installed). No browser verification in this task (map props are not wired in `index.vue` until Task 8).

## Deliverables Checklist

- [x] Props: `nowcastingEnabled?`, `selectedHorizon?`, `predictedCells?`, `nowcastModel?`
- [x] Sources: `nowcast-bbox`, `nowcast-points` (not rain-cell IDs)
- [x] Style: dashed teal outline `#2dd4bf`, fill opacity 0.15, circle `#2dd4bf`
- [x] Symbol label `+{forecast_minutes}m` on `nowcast-points-label`
- [x] Hidden when nowcasting off, horizon NOW (`0`), or no matching cells
- [x] Click popup (Vietnamese): Nowcasting, forecast minutes, probability %, intensity label, confidence %, movement, model Baseline v0.1, predicted disclaimer
- [x] Watcher mirrors rain-cell pattern; `renderAll` also syncs nowcast layers
- [x] Did not modify `index.vue`
- [x] Commit on feature branch

## Commit

| SHA | Subject |
|-----|---------|
| `ea673cc` | feat(nowcast): render predicted rain cells on map |

Commit via `git.exe -F` workaround (per machine constraint).

## Self-Review

### Correctness

- Observed rain-cell IDs/colors (yellow/red/orange) are unchanged.
- Visibility gate matches the brief; cells are also filtered by `forecast_minutes === selectedHorizon` so mixed payloads still show one horizon.
- Popup formats `rain_probability` / `confidence` as percents (API is 0–1).
- `nowcastModel` missing → label falls back to `Baseline v0.1`.

### Scope

- `RouteMap.vue` + small helpers in `nowcast.ts` only.

### Concerns (non-blocking)

- Extra layer IDs `nowcast-bbox-fill` (fill) and `nowcast-points-label` (symbol) were required to meet dashed outline + fill + horizon text; required IDs `nowcast-bbox` / `nowcast-points` are still present.
- `RouteMap.vue` is large (~700 lines); nowcast sync copies the rain-cell upsert pattern rather than extracting a shared helper.
- No unit tests and no in-browser pass; layers stay hidden until Task 8 passes props from `index.vue`.
- Optional props mean current `index.vue` usage stays valid; nowcast overlay is inert until wired.

## Files

| Path | Action |
|------|--------|
| `frontend/app/components/RouteMap.vue` | modified |
| `frontend/app/utils/nowcast.ts` | modified |

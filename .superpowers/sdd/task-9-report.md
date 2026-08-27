# Task 9 Report: RouteMap traffic layers + segment popup

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `2fd72b4` — `feat(traffic): render traffic segments on map`  
**Date:** 2026-08-25  
**Status:** DONE

## Scope

Implemented Task 9 per brief (`.superpowers/sdd/task-9-brief.md`):
- Modified `frontend/app/components/RouteMap.vue` — traffic GeoJSON line layer + click popup
- Minor fix in `frontend/app/utils/traffic.ts` — `percentLabel` unsigned for rain probability/confidence; signed for delta fields

Did not modify `index.vue` (Task 10).

### RouteMap changes

- New props: `trafficEnabled`, `trafficPredictionEnabled`, `trafficSelectedHorizon`, `trafficSegments`, `trafficPredictionsForHorizon`, `trafficModel`
- Source/layer IDs: `traffic-line` / `traffic-line-layer`
- Current mode when `trafficEnabled && (!trafficPredictionEnabled || trafficSelectedHorizon === 0)`
- Predicted mode when `trafficPredictionEnabled && trafficSelectedHorizon > 0`
- Paint: `line-color` from feature `color`; predicted dashed `[2, 1]` opacity 0.9; current solid opacity 0.95
- Click → `formatTrafficPopup` with dark popup styling (reuses rain/nowcast popup helper)
- Layer inserted before weather points so congestion colors show above route line
- Watcher + `renderAll` integration; rain/nowcast/radar/satellite behavior unchanged

## Verification

No frontend unit test runner in repo (per brief).

TypeScript check:

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

Commit via `C:/Program Files/Git/mingw64/bin/git.exe commit -F`.

## Deliverables Checklist

- [x] Traffic props on RouteMap
- [x] `traffic-line` / `traffic-line-layer` IDs (distinct from route/nowcast)
- [x] Current vs predicted visibility rules
- [x] Dashed predicted / solid current styling
- [x] Segment click popup via `formatTrafficPopup`
- [x] Existing rain/nowcast/radar layers preserved
- [x] `percentLabel` unsigned fix for probability/confidence
- [x] Commit on feature branch

## Files

| Path | Action |
|------|--------|
| `frontend/app/components/RouteMap.vue` | Modified |
| `frontend/app/utils/traffic.ts` | Modified (percentLabel) |

## Self-Review

### Correctness

- Follows nowcast `sync*` / watcher / click-bind-once pattern.
- Mode switch updates GeoJSON and dasharray without recreating source when possible.
- Predicted segments without horizon match are skipped by `trafficLineGeoJson` (Task 7).

### Concerns (non-blocking)

- `index.vue` not wired — traffic layer inactive until Task 10 passes props.
- No in-browser verification (no dev server in session).
- Blue route line still visible under traffic segments; traffic draws above route but both share path.

## Review Fix (z-order)

**Finding:** Traffic layer could render under route line when `renderRouteLayers()` ran after `syncTrafficLayer()` (e.g. radar/satellite watchers, `renderAll` ordering).

**Change (`RouteMap.vue`):**
- `syncTrafficLayer()` — `moveLayer(TRAFFIC_LINE_LAYER, beforeId)` when layer already exists
- `renderRouteLayers()` — call `syncTrafficLayer()` after route/weather layers are re-added
- `renderAll()` — route first, then traffic via `renderRouteLayers()`; `syncTrafficLayer()` only when no route

**Verification:**

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

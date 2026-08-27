# Task 8 Report: RadarControls — traffic toggles + traffic timeline

**Branch:** `feat/stage6-traffic-prediction`  
**Commit:** `32cf096` — `feat(traffic): add traffic toggles and prediction horizon UI`  
**Date:** 2026-08-25  
**Status:** DONE

## Scope

Implemented Task 8 per brief (`.superpowers/sdd/task-8-brief.md`):
- Extended `frontend/app/components/RadarControls.vue` only
- Props: `trafficEnabled`, `trafficPredictionEnabled`, `trafficLoading`, `trafficError`, `trafficModelLabel`, `trafficSelectedHorizon`, `trafficSegmentCount`
- Emits: `update:trafficEnabled`, `update:trafficPredictionEnabled`, `update:trafficSelectedHorizon`
- Vietnamese copy: **Giao thông**, **Dự báo giao thông**
- Traffic timeline `NOW +5m +10m +15m +30m` (no +60m) when `trafficPredictionEnabled && routeReady`
- Disclaimer: `Dự báo baseline v0.1 — giao thông synthetic (không phải live)`
- Placed after nowcasting block, before radar/satellite
- Separate `trafficHorizonOptions` / `TrafficSelectedHorizon` — does not reuse nowcast horizon props

Did not modify `RouteMap.vue` or `index.vue` (Tasks 9–10).

## Verification

No frontend unit test runner in repo (per brief).

TypeScript check:

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

Commit via `C:/Program Files/Git/mingw64/bin/git.exe commit -F` (cmd wrapper rejects `--trailer` on this machine).

## Deliverables Checklist

- [x] Two checkboxes with route-ready disable + helper text
- [x] Loading / error / segment count when either traffic toggle on + route ready
- [x] Prediction horizon buttons independent from nowcast timeline
- [x] Baseline synthetic disclaimer + optional `trafficModelLabel`
- [x] Commit on feature branch

## Files

| Path | Action |
|------|--------|
| `frontend/app/components/RadarControls.vue` | Modified |

## Self-Review

### Correctness

- Traffic UI mirrors nowcasting interaction patterns (checkboxes, horizon pills, disclaimer).
- Timeline excludes +60m per Stage 6 traffic spec.
- Status block shows when either toggle is active so prediction-only mode still surfaces loading/errors.

### Concerns (non-blocking)

- `index.vue` does not pass new props yet — UI inactive until Task 10 wiring.
- No in-browser verification (no running dev server in this session).
- `tsc` passes but runtime will warn until parent supplies required props.

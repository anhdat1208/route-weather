# Task 5 Report: Frontend types + useNowcasting

**Branch:** `feat/stage5-ai-nowcasting`  
**Date:** 2026-08-25  
**Status:** DONE

## Summary

Added client types mirroring `NowcastPredictionResponse` / `PredictedRainCell`, composable `useNowcasting` (POST `/api/nowcasting/predict`, horizon `0|5|10|15|30|60`, 300s refresh), and GeoJSON/intensity helpers. Did not modify RadarControls, RouteMap, or `index.vue`.

## TDD Evidence

No Jest in the frontend repo (plan/brief: verify by TypeScript). `npx nuxi typecheck` cannot run (`vue-tsc` not installed). App TypeScript check:

```text
$ cd frontend; npx tsc -p .nuxt/tsconfig.app.json --noEmit --pretty false
(exit 0, no diagnostics)
```

`npx nuxi prepare` succeeded with no duplicated-import warning after dropping a `bearingToCompass` re-export from `nowcast.ts`.

## Deliverables Checklist

- [x] `frontend/app/types/nowcasting.ts` — request/response, `NowcastSelectedHorizon` (`0` = NOW)
- [x] `frontend/app/composables/useNowcasting.ts` — `enabled`, `selectedHorizon` (`useState("nowcast-horizon")`), `loading`, `errorMessage`, `response`, `predictionsForHorizon`, `setEnabled`, `setHorizon`, `fetchNowcast`, 300s refresh
- [x] `predictionsForHorizon`: empty when NOW; else filter `forecast_minutes === selectedHorizon`
- [x] `frontend/app/utils/nowcast.ts` — `nowcastGeoJson`, `intensityLabel` (Không rõ / nhẹ / vừa / mạnh), reuses `bearingToCompass`
- [x] Did not modify RadarControls, RouteMap, or index.vue
- [x] Commit on feature branch

## Commit

| SHA | Subject |
|-----|---------|
| `270b8d9` | feat(nowcast): add frontend types and useNowcasting composable |

Commit via `git.exe -F` workaround (per machine constraint).

## Self-Review

### Correctness

- Types align with backend schemas (`kind: "predicted"`, motion, bounds, confidence, `radar_age_seconds`).
- Fetch/error/refresh copy `useRainCells` (`unavailable` does not schedule refresh; `partial`/`ok` refresh every 300s).
- Horizon is client-side filter; one API payload covers all forecast minutes.
- Intensity: `null` → `Không rõ`; `<40` nhẹ; `<90` vừa; else mạnh.

### Scope

- Three new frontend files only. Stage 1–4 UI untouched.

### Concerns (non-blocking)

- No unit tests (repo has no frontend Jest). Behavior of `predictionsForHorizon` / `intensityLabel` is not executed until Task 6–8 wire UI.
- `nuxi typecheck` needs `vue-tsc`; used `tsc -p .nuxt/tsconfig.app.json` instead.
- Same composable-instance caveat as rain cells: timer/`lastGeometry` are per `useNowcasting()` call (page should use once).

## Files

| Path | Action |
|------|--------|
| `frontend/app/types/nowcasting.ts` | created |
| `frontend/app/composables/useNowcasting.ts` | created |
| `frontend/app/utils/nowcast.ts` | created |

### Task 5: Frontend types + `useNowcasting`

**Files:**
- Create: `frontend/app/types/nowcasting.ts`
- Create: `frontend/app/composables/useNowcasting.ts`
- Create: `frontend/app/utils/nowcast.ts`

**Interfaces:**
- Mirror backend types (`NowcastPredictionResponse`, `PredictedRainCell`, horizons union)
- `useNowcasting()` returns: `enabled`, `selectedHorizon` (`0 | 5 | 10 | 15 | 30 | 60` where `0` = NOW), `loading`, `errorMessage`, `response`, `predictionsForHorizon` computed, `setEnabled`, `setHorizon`, `fetchNowcast(geometry)`, refresh every 300s when enabled
- `predictionsForHorizon`: filter `response.predictions` by `forecast_minutes === selectedHorizon` when horizon > 0; empty when NOW
- `utils/nowcast.ts`: `nowcastGeoJson(cells: PredictedRainCell[])`, `intensityLabel(intensity: number | null): string`, reuse `bearingToCompass` from `rainCell.ts`

- [ ] **Step 1: Add types + composable + utils** (no separate Jest in repo â€” verify by TypeScript usage and manual later)

`useNowcasting.ts` pattern copy from `useRainCells.ts` but endpoint `/api/nowcasting/predict` and keep `selectedHorizon` in `useState("nowcast-horizon", () => 0)`.

Intensity labels (Vietnamese): null â†’ `KhÃ´ng rÃµ`; `<40` nháº¹; `<90` vá»«a; else máº¡nh (thresholds aligned to RainViewer-ish scale).

- [ ] **Step 2: Commit**

Message: `feat(nowcast): add frontend types and useNowcasting composable`

---

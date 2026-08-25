### Task 7: RouteMap predicted layers + inspection panel

**Files:**
- Modify: `frontend/app/components/RouteMap.vue`
- Optionally small helper already in `utils/nowcast.ts`

**Interfaces:**
- New props: `nowcastingEnabled?: boolean`, `selectedHorizon?: number`, `predictedCells?: PredictedRainCell[]`, `nowcastModel?: { name: string; version: string } | null`
- Layers (distinct IDs): `nowcast-bbox`, `nowcast-points` â€” dashed line / teal fill opacity ~0.15, circle color `#2dd4bf`, text field `+{forecast_minutes}m` if MapLibre symbol feasible; otherwise popup only
- Show layers only when `nowcastingEnabled && selectedHorizon > 0 && predictedCells.length`
- Click â†’ popup Vietnamese fields: Nowcasting, forecast, probability %, intensity label, confidence %, movement, model Baseline v0.1, disclaimer predicted
- Do not reuse observed rain-cell layer IDs or colors (observed uses yellow/red)

- [ ] **Step 1: Implement GeoJSON update watchers mirroring rain-cell pattern in `RouteMap.vue`**

- [ ] **Step 2: Manual sanity (dev server) optional; ensure no TS errors in component

- [ ] **Step 3: Commit**

Message: `feat(nowcast): render predicted rain cells on map`

---

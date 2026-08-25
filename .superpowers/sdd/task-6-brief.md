### Task 6: RadarControls â€” toggle + timeline

**Files:**
- Modify: `frontend/app/components/RadarControls.vue`

**Interfaces:**
- New props: `nowcastingEnabled`, `nowcastingLoading`, `nowcastingError`, `nowcastingModelLabel`, `selectedHorizon`, `nowcastPredictionCount`, `routeReady` (already exists)
- Emits: `update:nowcastingEnabled`, `update:selectedHorizon`
- When `nowcastingEnabled && routeReady`, show timeline buttons: `NOW`, `+5m`, `+10m`, `+15m`, `+30m`, `+60m`
- Show small note: `Dá»± bÃ¡o baseline â€” khÃ´ng pháº£i radar quan sÃ¡t` + model label

- [ ] **Step 1: Extend props/emits/template** following existing rain-cells toggle markup (checkbox + status lines). Horizon buttons: highlight selected with existing accent classes.

- [ ] **Step 2: Commit**

Message: `feat(nowcast): add nowcasting toggle and horizon timeline UI`

---

### Task 8: RadarControls â€” traffic toggles + traffic timeline

**Files:**
- Modify: `frontend/app/components/RadarControls.vue`

**Interfaces:**
- New props: `trafficEnabled`, `trafficPredictionEnabled`, `trafficLoading`, `trafficError`, `trafficModelLabel`, `trafficSelectedHorizon`, `trafficSegmentCount`
- Emits: `update:trafficEnabled`, `update:trafficPredictionEnabled`, `update:trafficSelectedHorizon`
- Copy: **Giao thÃ´ng**, **Dá»± bÃ¡o giao thÃ´ng**
- Timeline only when `trafficPredictionEnabled && routeReady`: `NOW +5m +10m +15m +30m` (no +60m)
- Disclaimer: `Dá»± bÃ¡o baseline v0.1 â€” giao thÃ´ng synthetic (khÃ´ng pháº£i live)`
- Do **not** reuse nowcast `selectedHorizon` / nowcast timeline buttons

Place the two checkboxes after nowcasting block, before radar/satellite (keep weather-layer grouping readable).

- [ ] **Step 1: Extend template + props/emits**

- [ ] **Step 2: Commit**

Message: `feat(traffic): add traffic toggles and prediction horizon UI`

---


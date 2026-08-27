### Task 9: RouteMap traffic layers + segment popup

**Files:**
- Modify: `frontend/app/components/RouteMap.vue`

**Interfaces:**
- New props: `trafficEnabled`, `trafficPredictionEnabled`, `trafficSelectedHorizon`, `trafficSegments`, `trafficPredictionsForHorizon`, `trafficModel`
- Source/layer IDs: `traffic-line` / `traffic-line-layer` only (do not reuse route-line or nowcast IDs)
- Show current colors when `trafficEnabled && (!trafficPredictionEnabled || trafficSelectedHorizon===0)`
- Show predicted colors when `trafficPredictionEnabled && trafficSelectedHorizon>0`
- Paint: `line-color` from feature property `color`; predicted: `line-dasharray: [2, 1]`, opacity ~0.9; current: solid
- Click â†’ popup via `formatTrafficPopup`
- Keep existing rain/nowcast/radar behavior unchanged

Follow existing `ensureSource` / watcher pattern used for nowcast layers.

- [ ] **Step 1: Implement layers + click handler**

- [ ] **Step 2: Commit**

Message: `feat(traffic): render traffic segments on map`

---


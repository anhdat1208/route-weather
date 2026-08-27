### Task 7: Frontend types + `useTraffic` + GeoJSON utils

**Files:**
- Create: `frontend/app/types/traffic.ts`
- Create: `frontend/app/composables/useTraffic.ts`
- Create: `frontend/app/utils/traffic.ts`

**Interfaces:**
- Mirror backend types. `TrafficHorizon = 5 | 10 | 15 | 30`. `TrafficSelectedHorizon = 0 | TrafficHorizon`.
- `useTraffic()`: `enabled` (`useState("traffic-enabled")`), `predictionEnabled` (`useState("traffic-prediction-enabled")`), `selectedHorizon` (`useState("traffic-horizon")` default 0), `loading`, `errorMessage`, `response`, `setEnabled`, `setPredictionEnabled`, `setHorizon`, `fetchTraffic(geometry)`.
- Fetch when **either** toggle is on and geometry length â‰¥ 2. Endpoint `POST /api/traffic/prediction`. Refresh 300s. If `status==="unavailable"` set error from message.
- `predictionsForHorizon`: filter `predictions` by `forecast_minutes === selectedHorizon` when horizon > 0.
- Utils:
  - `congestionColor(level)`: free `#22c55e`, slow `#eab308`, moderate `#f97316`, heavy `#ef4444`, severe `#991b1b`, null `#64748b`
  - `trafficLineGeoJson(segments, predictionsForHorizon, mode: "current" | "predicted")`
  - `formatTrafficPopup(...)` Vietnamese fields matching spec panel + synthetic disclaimer
  - `trafficModelLabel` like nowcast

Predicted GeoJSON: use `predicted_congestion` / `predicted_speed_kmh` from the matching prediction; skip segments without a prediction.

- [ ] **Step 1: Add files** (no frontend unit test runner in repo)

- [ ] **Step 2: Commit**

Message: `feat(traffic): add frontend types and useTraffic composable`

---


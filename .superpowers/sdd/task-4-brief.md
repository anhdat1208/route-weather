### Task 4: WeatherImpactModel

**Files:**
- Create: `backend/app/engine/weather_impact.py`
- Create: `backend/tests/test_weather_impact.py`

**Interfaces:**
- Consumes: `RoadSegmentOut`, `NowcastPredictionResponse` / `PredictedRainCell`, `min_distance_to_polyline_m`, `settings.traffic_rain_nearby_km`
- Produces: `estimate_impact(segment, *, horizon: int, nowcast: NowcastPredictionResponse | None) -> WeatherImpactInfo`

**Algorithm (lock):**

```text
If nowcast is None or status == "unavailable" or predictions empty:
  return speed_delta_pct=0, level="none", reasons=["no_rain_prediction"]
    (if unavailable: reasons=["nowcast_unavailable"])

cells = predictions where forecast_minutes == horizon
nearby = cells whose centroid is within traffic_rain_nearby_km of segment.geometry
If none: level none, delta 0, reasons=["no_rain_nearby"]

Pick cell with max rain_intensity (None treated as 0)
intensity bands (same as frontend nowcast labels):
  < 40 â†’ low,   base_delta = -0.07
  < 90 â†’ moderate, base_delta = -0.15
  else â†’ high,  base_delta = -0.25
If intensity is None: treat as light (low)

delta = base_delta
if rain_probability is not None: delta *= rain_probability
delta *= clamp(cell.confidence, 0, 1)
if current congestion in {heavy, severe}: delta *= 0.5; reasons += ["already_congested"]
if cell.confidence < 0.4: reasons += ["low_nowcast_confidence"]
reasons += ["light_rain_nearby" | "moderate_rain_nearby" | "heavy_rain_nearby"]
return WeatherImpactInfo(...)
```

- [ ] **Step 1: Write failing tests** covering: no rain, light, heavy, already congested, low confidence cell, unavailable nowcast. Build tiny `NowcastPredictionResponse` + one `RoadSegmentOut` helpers in the test file.

- [ ] **Step 2: Run â€” expect fail**

- [ ] **Step 3: Implement `estimate_impact`**

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

Message: `feat(traffic): add rule-based weather impact model`

---


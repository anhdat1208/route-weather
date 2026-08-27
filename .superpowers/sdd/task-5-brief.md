### Task 5: TrafficPredictionEngine (combine + confidence + status)

**Files:**
- Create: `backend/app/engine/traffic_engine.py`
- Create: `backend/tests/test_traffic_engine.py`

**Interfaces:**
- Consumes: segments, base pairs from `BaselineTrafficModel`, impact from `WeatherImpactModel`, nowcast response
- Produces: `run_traffic_prediction(segments, *, nowcast, at) -> TrafficPredictionResponse`

**Combine (lock):**

```text
adjusted_speed = clamp(base_speed * (1 + weather_impact.speed_delta_pct), free_flow)
weather_adjusted.speed_delta_pct = (adjusted / current) - 1  if current else None
predicted_* = weather_adjusted
```

**Confidence (lock):**

```text
c = settings.traffic_base_confidence  # 0.75
if traffic.stale: c *= 0.7
if current_speed is None: c *= 0.5
c *= max(0.35, 1.0 - 0.012 * horizon)   # 5mâ‰ˆ0.94, 30mâ‰ˆ0.64 times base
if nowcast_status not in {"ok", "skipped"} and impact.level != "none": c *= 0.75
if "low_nowcast_confidence" in reasons: c *= 0.85
if "no_history" always true in Stage 6: c *= 0.9
clamp [0, 1]
```

**Status:**

| Condition | status | nowcast_status | message |
|---|---|---|---|
| no segments | unavailable | skipped | Vietnamese: khÃ´ng cÃ³ Ä‘oáº¡n Ä‘Æ°á»ng |
| some missing current speed | partial | (from nowcast) | má»™t sá»‘ Ä‘oáº¡n thiáº¿u tá»‘c Ä‘á»™ |
| nowcast unavailable | ok (base still returned) | unavailable | thá»i tiáº¿t dá»± bÃ¡o khÃ´ng kháº£ dá»¥ng; dÃ¹ng dá»± bÃ¡o giao thÃ´ng ná»n |
| else | ok | nowcast.status or skipped | None |

Engine **must** still emit base predictions when nowcast is unavailable (impact 0).

- [ ] **Step 1: Write tests**
  - combine: base 28, impact âˆ’20% â†’ 22.4 (allow float tolerance)
  - confidence lower at 30m than 5m
  - stale traffic lowers confidence
  - empty segments â†’ unavailable
  - nowcast unavailable â†’ predictions non-empty, impact 0, nowcast_status unavailable
  - heavy rain reduces adjusted vs base

- [ ] **Step 2: Run â€” expect fail**

- [ ] **Step 3: Implement `run_traffic_prediction`**

Use `BaselineTrafficModel()` and `estimate_impact`. Horizons from `settings.traffic_horizons_minutes`. Model info from settings.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

Message: `feat(traffic): add traffic prediction engine`

---


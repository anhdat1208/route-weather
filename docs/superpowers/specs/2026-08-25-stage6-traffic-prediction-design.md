# Route Weather Stage 6 — Traffic Prediction & Weather Impact — Design Specification

> Approved: 2026-08-25  
> Approach: **Engine + BaselineTrafficModel + WeatherImpactModel** (Approach 1)  
> Builds on Stage 1–5 (Route Weather MVP, Live Radar, Rain-cell Tracking, Satellite Fusion, AI Nowcasting)

## 1. Product Goal

Stage 5 answers: *"Where will rain cells likely be in the next 5–60 minutes?"*

Stage 6 begins answering: *"How may that predicted rain affect traffic on this route?"*

```text
Weather Prediction (Stage 5 nowcast)
        +
Traffic Data
        ↓
Base Traffic Prediction
        +
Weather Impact (separate)
        ↓
Weather-adjusted Traffic Prediction
        ↓
API + Map Visualization
```

The system evolves from:

```text
"Rain will occur here in 15 minutes."
```

into:

```text
"Rain will occur here in 15 minutes,
and traffic on these road segments
is likely to become slower."
```

The first traffic model is a **baseline** (trend / time-of-day heuristics + rule-based weather impact), not a validated ML traffic predictor. It establishes the modular pipeline so a future live traffic provider and/or ML model can replace pieces without rewriting the API or frontend.

## 2. Decisions Locked

| Topic | Decision |
|---|---|
| Traffic data source | **Hybrid**: `TrafficProvider` Protocol + `SyntheticTrafficProvider` default; live providers (GraphHopper traffic / TomTom / HERE / …) plug in later without contract changes |
| Road representation | **Hybrid light**: stable `RoadSegment` interface; Stage 6 builds segments from the existing route polyline samples (`route-seg-{index}`); not a full road network / routing graph |
| Weather input | Backend **auto-invokes** Stage 5 `NowcastingEngine` inside traffic prediction (client sends `geometry` only) |
| Architecture | Approach 1 — Engine + Baseline + separate Weather Impact |
| API | `POST /api/traffic/prediction` returning current segments + multi-horizon predictions |
| First models | `BaselineTrafficModel` (`name=baseline`, `version=0.1`) + rule-based `WeatherImpactModel` |
| Horizons | Fixed: **5, 10, 15, 30** minutes (no +60m in Stage 6 traffic UI; nowcast may still use its own horizons internally) |
| Separation | Always keep **base prediction**, **weather impact**, and **weather-adjusted** distinct in the response |
| UI | Toggles for Traffic + Traffic Prediction in `RadarControls`; horizon timeline; segment detail panel; distinct MapLibre layers |
| Stage 7 | Out of scope — no route optimization / traffic-aware ETA productization |
| Git branch | `feat/stage6-traffic-prediction` from `main` |

## 3. Existing Stage 1–5 Context (constraints)

| Item | Current state |
|---|---|
| Unified weather | `WeatherFusionResponse` / `FusedSegmentState` (no type named `WeatherState`) |
| Nowcasting | `POST /api/nowcasting/predict` → `NowcastPredictionResponse` / `PredictedRainCell`; engine + `BaselineExtrapolationModel` |
| Route geometry | GraphHopper polyline → sampled segments (`RouteWeatherSegment`, fusion segment start/end) |
| Road network | **None** beyond route polyline samples |
| Live traffic speeds | **None** — GraphHopper used for route/geocode only today |
| Frontend | Nuxt / Vue: `useRadar`, `useRainCells`, `useNowcasting`, `useWeatherFusion`, `RouteMap`, `RadarControls` |
| Backend pattern | FastAPI routers; POST + Pydantic; `providers/` Protocol; `engine/` algorithms; `services/` orchestration |
| Naming | snake_case JSON; `lat`/`lng`; response `status: ok \| partial \| unavailable` |

**Do not rewrite or replace Stage 1–5.** Radar, rain cells, fusion, and nowcasting must keep working when traffic layers are off.

## 4. System Architecture

```text
Route geometry (client)
        ↓
POST /api/traffic/prediction
        ↓
TrafficService
        ├── TrafficProvider.for_route(geometry)
        │         ↓
        │   RoadSegment[] + TrafficState (current)
        ├── BaselineTrafficModel.predict(...)
        │         ↓
        │   base TrafficPrediction per segment × horizon
        ├── NowcastingService / NowcastingEngine (Stage 5 reuse)
        │         ↓
        │   rain predictions (internal; not a second weather system)
        └── WeatherImpactModel.estimate(...)
                  ↓
            weather impact per segment × horizon
        ↓
TrafficPredictionEngine.combine(...)
        ↓
TrafficPredictionResponse
        ↓
useTraffic → RouteMap traffic layers + timeline + segment panel
```

### Responsibility boundaries

| Layer | Does | Does not |
|---|---|---|
| `TrafficProvider` | Produce current `RoadSegment` + `TrafficState` | Forecast or weather math |
| `SyntheticTrafficProvider` | Deterministic demo traffic from route + ToD heuristics | Claim live observations |
| `BaselineTrafficModel` | Extrapolate base speeds / congestion by horizon | Call weather/nowcast APIs |
| `WeatherImpactModel` | Rule-based speed delta % from rain nowcast + context | Replace base traffic |
| `TrafficPredictionEngine` | Select models, combine, normalize, confidence | Provider HTTP / Vue logic |
| `TrafficService` / API | Orchestrate request → response; invoke nowcast internally | Frontend business logic |
| `useTraffic` | Fetch, cache, selected horizon | Run prediction math |
| `RouteMap` / controls | Draw segments; timeline; panel | Algorithms |

### Future insertion points

```text
TrafficProvider
  ├── SyntheticTrafficProvider     ← Stage 6 default
  ├── GraphHopperTrafficProvider   ← future (if plan supports)
  └── TomTomTrafficProvider / …    ← future live

TrafficPredictionModel
  ├── BaselineTrafficModel         ← Stage 6
  ├── MLTrafficModel               ← future
  └── DeepLearningTrafficModel     ← future
```

Engine (or thin factory) selects active provider/model by config. API response always includes `model.name` + `model.version` and per-segment `traffic.source`. Frontend and API contract stay stable across swaps.

Conceptual pipeline:

```text
Weather State / Rain cells
     ↓
AI Nowcasting
     ↓
Rain Prediction
     ↓
      ┌───────────────────┐
      │ Weather Impact    │  ← rule-based baseline (Stage 6)
      └───────────────────┘
                ↓
Traffic Data ──────────→ Base Traffic Prediction
                ↓
       Weather-adjusted Traffic
                ↓
             Map
```

Label clearly which values are **observed** (or synthetic-current), **base predicted**, **weather impact**, and **weather-adjusted**.

## 5. Normalized Data Models

Adapt names to existing Pydantic / TypeScript conventions.

### Request

```typescript
interface TrafficPredictRequest {
  geometry: { lat: number; lng: number }[]  // min 2
  buffer_km?: number                        // optional; corridor semantics aligned with rain/nowcast
}
```

### Core types

```typescript
type CongestionLevel = "free" | "slow" | "moderate" | "heavy" | "severe"

interface RoadSegment {
  id: string                    // e.g. "route-seg-0"
  geometry: { lat: number; lng: number }[]  // typically start+end of sample edge
  road_type?: "arterial" | "local" | "unknown" | string | null
  name?: string | null
  traffic: TrafficState | null
}

interface TrafficState {
  current_speed_kmh: number | null
  free_flow_speed_kmh: number | null
  congestion_level: CongestionLevel | null
  relative_speed: number | null   // current / free_flow when both known
  timestamp: string               // ISO
  source: "synthetic" | string
  stale: boolean
}

interface TrafficModelInfo {
  name: "baseline" | string
  version: string                 // e.g. "0.1"
}

interface SpeedCongestionPair {
  speed_kmh: number | null
  congestion: CongestionLevel | null
  speed_delta_pct?: number | null // vs current or vs free-flow; document in field use
}

interface WeatherImpactInfo {
  speed_delta_pct: number         // e.g. -0.15 = -15%
  level: "none" | "low" | "moderate" | "high"
  rain_probability: number | null // 0–1 when available
  rain_intensity: number | null
  reasons: string[]               // short explainability codes/messages
}

interface TrafficPrediction {
  road_segment_id: string
  forecast_minutes: 5 | 10 | 15 | 30
  predicted_speed_kmh: number | null      // weather-adjusted (primary map value)
  predicted_congestion: CongestionLevel | null
  confidence: number                      // 0–1
  base_prediction: SpeedCongestionPair
  weather_impact: WeatherImpactInfo
  weather_adjusted: SpeedCongestionPair
  model: TrafficModelInfo
}

interface TrafficPredictionResponse {
  generated_at: string
  status: "ok" | "partial" | "unavailable"
  model: TrafficModelInfo
  horizons: number[]                      // [5, 10, 15, 30]
  segments: RoadSegment[]                 // current traffic snapshot
  predictions: TrafficPrediction[]
  nowcast_status: "ok" | "partial" | "unavailable" | "skipped"
  message?: string | null
}
```

### Provenance rules

- Synthetic current traffic must set `source: "synthetic"` and UI copy must not claim live traffic.
- Baseline predictions must expose `model.name=baseline` / `version=0.1`.
- Never present baseline output as validated AI traffic accuracy.
- `predicted_speed_kmh` is always the **weather-adjusted** value used for map coloring when prediction mode is on.
- Do not fabricate traffic measurements when the provider has no data.

## 6. Algorithms

### 6.1 Synthetic current traffic (`SyntheticTrafficProvider`)

Purpose: unblock the full pipeline without a paid live feed.

- Build `RoadSegment`s from consecutive route geometry samples (reuse sampler spacing conventions where practical).
- Assign `free_flow_speed_kmh` from a simple heuristic (e.g. by optional `road_type`, else a conservative default such as urban arterial range).
- Assign `current_speed_kmh` from free-flow modulated by **time of day** and **day of week** curves (deterministic for a given timestamp + segment index so tests are stable).
- Optionally add mild along-route variation (seeded by segment index) — not random noise per request.
- Derive `congestion_level` and `relative_speed` from current vs free-flow thresholds.
- Set `stale=false` for freshly generated synthetic snapshots; if a future cache layer serves old snapshots, mark `stale=true` when age exceeds a configured threshold.

### 6.2 Baseline traffic prediction (`BaselineTrafficModel`)

Inputs: current `TrafficState`, optional recent trend (if provider supplies history; Stage 6 synthetic may omit true history), time of day, day of week, horizon minutes.

Per segment × horizon:

1. Start from `current_speed_kmh` (or free-flow if current missing → low confidence / partial).
2. Apply a small ToD drift toward expected pattern at `now + horizon`.
3. If a short trend is available, extrapolate linearly with dampening; clamp so speeds stay within a safe band relative to free-flow (e.g. not above free-flow × 1.05, not below a minimum floor).
4. Map speed → `congestion_level`.
5. Emit `base_prediction` only (no weather).

Missing historical traffic → hold near current + reduce confidence (do not invent a rich history).

### 6.3 Weather impact (`WeatherImpactModel`)

Inputs: Stage 5 predicted rain near the segment (distance / coverage heuristic), rain intensity, rain probability, horizon, current congestion, optional `road_type`, nowcast confidence.

Suggested baseline intensity bands (tunable constants, not calibrated science):

| Rain context | Impact level | Indicative `speed_delta_pct` |
|---|---|---|
| No rain / far from cells | `none` | ~0 |
| Light | `low` | about −0.05 to −0.10 |
| Moderate | `moderate` | about −0.10 to −0.20 |
| Heavy | `high` | larger negative, still clamped |

Rules:

- **Do not** assume rain always causes congestion everywhere.
- If traffic is already `heavy`/`severe`, additional weather impact is dampened (diminishing returns).
- If free-flow and no rain nearby → impact stays `none`.
- Low nowcast confidence or `nowcast_status` not `ok` → shrink impact magnitude and lower traffic prediction confidence.
- Attach short `reasons[]` (e.g. `heavy_rain_nearby`, `low_nowcast_confidence`, `already_congested`).

### 6.4 Combine (explainable)

```text
weather_adjusted_speed = base_speed × (1 + weather_impact.speed_delta_pct)
```

Then re-derive congestion from adjusted speed. Populate:

- `base_prediction`
- `weather_impact`
- `weather_adjusted`
- top-level `predicted_speed_kmh` / `predicted_congestion` = weather-adjusted

Panel math example:

```text
Base traffic trend:     -8%
Weather impact:        -15%
Combined slowdown:     ~-23%  (from composing factors; show both components)
```

Exact combined-% display may be computed as  
`(adjusted / current) - 1` while still listing the two components separately.

### 6.5 Confidence

Start from a base score (e.g. 0.75 for fresh synthetic, higher later for live feeds). Multiply / subtract for:

- stale traffic
- missing / insufficient history
- unstable recent trend (when available)
- longer horizons
- low nowcast confidence / unavailable nowcast when weather term is non-zero
- missing current speed

Clamp to `[0, 1]`. Keep the formula simple and documented in code comments / tests.

### 6.6 Status & fallbacks

| Situation | Behavior |
|---|---|
| Provider returns no segments | `status=unavailable`, empty lists, clear `message` |
| Some segments missing speed | Predict where possible; `partial`; omit or null fields where not |
| Stale traffic | May still predict from last state; `stale=true`; lower confidence |
| Nowcast unavailable / no rain cells | `nowcast_status` reflects that; weather impact ≈ 0; **still return base predictions** |
| Low-confidence nowcast | Conservative impact; lower confidence |
| Prediction unreliable | Fall back toward current speed; mark `partial` / lower confidence — do not invent sensors |

Never fabricate live traffic observations. Synthetic values are allowed only via the explicit synthetic provider and must be labeled.

## 7. API

| Method | Path | Body |
|---|---|---|
| POST | `/api/traffic/prediction` | `TrafficPredictRequest` |

- Register router in `main.py` with try/except isolation (same pattern as rain-cells / nowcasting) so Stage 6 load failure does not take down Stage 1–5.
- Internally call existing nowcasting path (service/engine) — do **not** duplicate rain-cell tracking logic.
- Errors follow existing patterns (`422` validation, `503`/`502` where appropriate for upstream failure).
- Optional light in-process caching of identical geometry within a short TTL is allowed only if it matches existing project patterns; no new Redis/infra in Stage 6.

Do **not** overload `POST /api/route-weather`, `POST /api/weather-fusion/state`, or `POST /api/nowcasting/predict` with traffic payloads.

A separate `/api/traffic/current` endpoint is **not required** in Stage 6 (current snapshot is included in the prediction response).

## 8. Frontend Integration

### Toggles & timeline

Extend `RadarControls` (same interaction language; Vietnamese UI copy):

- **Giao thông** — show current traffic segment colors when enabled  
- **Dự báo giao thông** — when enabled and route geometry exists, `useTraffic` calls `POST /api/traffic/prediction`  
- Horizon timeline when prediction is ON:

```text
NOW ── +5m ── +10m ── +15m ── +30m
```

- `NOW`: current `TrafficState` congestion colors  
- Selected horizon ≠ `NOW`: weather-adjusted predicted congestion for that horizon  
- Disclaimer badge: **Baseline v0.1 — synthetic traffic (không phải live)**

Existing Weather / Rain cells / Nowcasting / Radar / Satellite toggles remain unchanged in behavior.

### Map layers

- New MapLibre sources/layers for traffic polylines (distinct IDs from radar, rain cells, nowcast).
- Color by congestion: free → green, slow → yellow, moderate → orange, heavy/severe → red (align with existing design tokens where possible).
- Predicted mode: visually distinguishable from current (e.g. slightly dashed stroke and/or different opacity) — not identical to nowcast teal rain styling.

### Segment panel

On selecting a road segment, show a compact panel (not a large dashboard):

- Road name / segment id  
- Current speed & congestion  
- Predicted speed & congestion for selected horizon  
- Weather impact level + rain probability/intensity when available  
- Confidence  
- Model baseline v0.1  
- Explainability: base trend %, weather impact %, combined effect  

### Composable

`useTraffic`: `enabled`, `predictionEnabled` (or equivalent), `selectedHorizon`, loading/error, response cache; refresh on route change and a polite interval (~5 minutes, same order as rain/nowcast). Do not recompute in map render loops.

## 9. Performance

- All prediction math runs in backend engines/services, not in Vue render loops.
- One traffic request may invoke one internal nowcast; reuse that nowcast result for all segments in the request (do not call nowcast per segment).
- Avoid unnecessary recalculation; cache composable response until route/geometry changes or refresh interval elapses.
- Do not introduce complex infrastructure unless required.

## 10. Testing

Minimum backend coverage:

1. Traffic-state normalization (speed → congestion / relative_speed)  
2. Horizons generated: 5 / 10 / 15 / 30  
3. Baseline traffic prediction behavior  
4. Weather impact: no rain, light, moderate, heavy  
5. Weather-adjusted combine math  
6. Confidence decreases with horizon / stale / low nowcast confidence  
7. Stale traffic handling  
8. Missing traffic / empty provider handling  
9. Low-confidence / unavailable nowcast → conservative impact + base still returned  
10. API response structure (schema / endpoint with mocked service & mocked nowcast)

Edge cases: free-flow + rain; already congested + heavy rain; missing history; stale weather/nowcast; empty geometry rejected by validation.

## 11. Documentation & Delivery

- This design file is the Stage 6 architecture source of truth.
- README roadmap: mark Stage 6 in progress / done when implementation lands.
- Implementation plan follows after this spec is user-reviewed.
- Clarify observed vs predicted vs baseline vs weather-adjusted in README/architecture notes.

## 12. Out of Scope / Non-goals

- Rewriting Stage 1–5 or replacing the Nowcasting Engine  
- Building a complete road graph / routing engine (Stage 7)  
- Traffic-aware multi-route optimization / ETA product (Stage 7)  
- Training neural networks / large ML pipelines without appropriate data  
- Assuming rain always causes congestion  
- Fabricating live traffic measurements or claiming validated accuracy  
- Second weather/nowcast system  
- Large new dashboards beyond toggle + timeline + segment panel  
- New paid traffic API integration in Stage 6 (provider slot only)

## 13. Acceptance Criteria

Stage 6 is complete when:

- [ ] Stage 1–5 functionality still works with traffic layers off  
- [ ] Modular `TrafficProvider` + `RoadSegment` / `TrafficState` exist  
- [ ] Synthetic default provider produces labeled current traffic  
- [ ] Current traffic can be visualized on the map  
- [ ] `BaselineTrafficModel` (`baseline` / `0.1`) produces horizons 5/10/15/30  
- [ ] Stage 5 nowcast influences traffic via separate `WeatherImpactModel`  
- [ ] Weather-adjusted prediction exists and is distinct from base  
- [ ] Predictions include confidence  
- [ ] `POST /api/traffic/prediction` returns normalized response  
- [ ] Frontend can toggle traffic / traffic prediction and switch horizons  
- [ ] Selected segments expose explainable prediction details  
- [ ] Missing/stale data handled without fabrication  
- [ ] Core prediction logic has tests  
- [ ] Architecture is ready for future live providers and ML traffic models  

## 14. Files Likely Touched (implementation preview)

**Backend (new):**  
`providers/base.py` (extend Protocol), `providers/synthetic_traffic.py`, `schemas/traffic.py`, `engine/traffic_models.py`, `engine/weather_impact.py`, `engine/traffic_engine.py`, `services/traffic_service.py`, `api/traffic.py`, `tests/test_traffic_*.py`

**Backend (modify):**  
`main.py` (router registration), possibly `config.py` for horizons / stale thresholds / free-flow defaults

**Frontend (new/modify):**  
`types/traffic.ts`, `composables/useTraffic.ts`, utils for traffic GeoJSON, `RadarControls.vue`, `RouteMap.vue`, `pages/index.vue`

**Docs:**  
this spec; later implementation plan; README Stage 6 note

## 15. What Stage 7 Can Build On

- Normalized per-segment current + predicted traffic with weather adjustment  
- Stable `RoadSegment` ids along a route corridor  
- Pluggable live `TrafficProvider` without rewriting FE  
- Explainable weather impact term for routing cost functions  
- Confidence signals for risk-aware ETA / alternate route scoring  

Stage 7 should consume this layer — not reimplement traffic prediction inside the router.

## 16. Known Limitations (accepted)

- Default traffic is **synthetic**, not live sensor/API traffic  
- Weather impact is transparent **rules**, not calibrated causal ML  
- Segments are route-polyline samples, not a city-wide road network  
- No historical traffic warehouse in Stage 6  
- Confidence is heuristic, not probability-calibrated  
- Traffic prediction accuracy is **not** validated for operational decisions  

Live providers and ML models can replace synthetic/baseline components later without changing the public prediction contract.

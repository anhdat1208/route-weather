# Route Weather Stage 5 — AI Nowcasting Engine — Design Specification

> Approved: 2026-08-25  
> Approach: **Engine + BaselineExtrapolationModel** (Approach 1)  
> Builds on Stage 1–4 (Route Weather MVP, Live Radar, Rain-cell Tracking, Satellite Fusion)

## 1. Product Goal

Stage 3–4 answer: *"Where are rain cells now, and how are they moving / fused with other sources?"*

Stage 5 begins answering: *"Where will those rain cells likely be in the next 5–60 minutes?"*

```text
Current Weather State (observed)
        +
Rain-cell Tracking (Stage 3)
        ↓
Nowcasting Engine
        ↓
Baseline Model (extrapolation)
        ↓
Future Rain Prediction
        ↓
API + Map Visualization
```

The first model is a **baseline motion extrapolation**, not a trained deep-learning nowcaster. It establishes the modular pipeline so a future ML/DL model can replace the baseline without rewriting the API or frontend.

## 2. Decisions Locked

| Topic | Decision |
|---|---|
| Primary input | Tracked rain cells only (reuse Stage 3 `RainCellService`) — not fusion segments |
| API | New `POST /api/nowcasting/predict` with `{ geometry, buffer_km? }`; backend tracks then predicts |
| Model architecture | Pluggable `NowcastingModel` behind `NowcastingEngine` |
| First model | `BaselineExtrapolationModel` — `name=baseline`, `version=0.1` |
| Horizons | Fixed: 5, 10, 15, 30, 60 minutes |
| UI activation | Separate “Nowcasting” toggle in `RadarControls` + timeline when ON |
| Map | Distinct predicted layers (not identical to live radar / observed rain cells) |
| Fusion | Do not require `/api/weather-fusion/state` for Stage 5 predict path |
| Second tracker | Forbidden — reuse existing rain-cell tracking |
| Deep learning / training | Out of scope for Stage 5 |
| Route risk / ETA impact | Out of scope |
| Git branch | `feat/stage5-ai-nowcasting` from `main` |

## 3. Existing Stage 1–4 Context (constraints)

| Item | Current state |
|---|---|
| Unified weather | `WeatherFusionResponse` / `FusedSegmentState` via `POST /api/weather-fusion/state` (no type named `WeatherState`) |
| Rain cells | `POST /api/rain-cells/track` → `TrackedRainCellOut` with centroid, bounds, intensity, area, `motion.speed_kmh` / `bearing_degrees` / `confidence`, `history` |
| Growth rate | Not a first-class field; may be inferred from `history` or fall back conservatively |
| Fusion features | `SegmentNowcastFeatures` describe **present** state only — not forecasts |
| Frontend | Nuxt / Vue: `useRadar`, `useRainCells`, `useWeatherFusion`, `RouteMap`, `RadarControls` |
| Map | MapLibre layers for radar, satellite, rain-cell bbox/points/motion |
| Backend pattern | FastAPI routers; heavy work via POST + Pydantic; engines under `app/engine`, services under `app/services` |

**Do not rewrite or replace Stage 1–4.** Rain-cell and radar overlays must keep working when nowcasting is off.

## 4. System Architecture

```text
Route geometry (client)
        ↓
POST /api/nowcasting/predict
        ↓
NowcastingService
        ↓
RainCellService.track_for_route   ← Stage 3 reuse
        ↓
NowcastingEngine
        ↓
NowcastingModel (protocol/interface)
        ↓
BaselineExtrapolationModel (v0.1)
        ↓
NowcastPredictionResponse
        ↓
useNowcasting → RouteMap predicted layers + timeline + info panel
```

### Responsibility boundaries

| Layer | Does | Does not |
|---|---|---|
| `RainCellService` | Detect/track cells for corridor | Future prediction |
| `NowcastingEngine` | Select model, run predict, normalize output | Provider HTTP / tile decode |
| `BaselineExtrapolationModel` | Extrapolate position, intensity, confidence | Call external weather APIs |
| `NowcastingService` / API | Orchestrate request → response | Vue business logic |
| `useNowcasting` | Fetch, cache state, selected horizon | Run extrapolation math |
| `RouteMap` / controls | Draw predicted geometry; timeline; panel | Algorithms |

### Future model insertion point

```text
NowcastingModel
  ├── BaselineExtrapolationModel   ← Stage 5
  ├── MLModel                      ← future
  └── DeepLearningModel            ← future
```

Engine (or thin factory) selects the active model by config. API response always includes `model.name` + `model.version`. Frontend and API contract stay stable across model swaps.

## 5. Normalized Prediction Models

Adapt names to existing Pydantic / TypeScript conventions (`lat`/`lng`, snake_case in API JSON as elsewhere).

### Request

```typescript
interface NowcastPredictRequest {
  geometry: { lat: number; lng: number }[]  // min 2
  buffer_km?: number                        // optional; same semantics as rain-cells
}
```

### Response

```typescript
interface NowcastModelInfo {
  name: "baseline" | string
  version: string  // e.g. "0.1"
}

interface PredictedRainCell {
  cell_id: string
  forecast_minutes: 5 | 10 | 15 | 30 | 60
  kind: "predicted"                         // never "observed"
  centroid: { lat: number; lng: number }
  bounds?: { north: number; south: number; east: number; west: number }
  rain_probability: number | null           // 0–1
  rain_intensity: number | null             // projected mean intensity scale
  confidence: number                        // 0–1
  motion?: {
    speed_kmh: number | null
    bearing_degrees: number | null
  }
  source: "rain_cell_track+baseline" | string
  // Reserved for later without breaking clients:
  // rain_rate?, predicted_area_km2?, uncertainty?, cell_velocity?, cell_direction?
}

interface NowcastPredictionResponse {
  generated_at: string
  status: "ok" | "partial" | "unavailable"
  model: NowcastModelInfo
  frames_used: number
  radar_age_seconds?: number | null
  horizons: number[]                        // [5, 10, 15, 30, 60]
  predictions: PredictedRainCell[]
  message?: string | null
}
```

Provenance rules:

- Every prediction item has `kind: "predicted"`.
- UI and copy must distinguish **Observed** (radar / tracked cells) vs **Predicted** (nowcast).
- Never present baseline output as validated scientific AI accuracy.

## 6. Baseline Extrapolation Algorithm

Constants:

- Horizons: `[5, 10, 15, 30, 60]` minutes  
- Model: `baseline` / `0.1`

Per tracked cell eligible for prediction (`TRACKING` or `NEW` with usable `current`):

1. **Position**  
   - If `motion.speed_kmh` and `motion.bearing_degrees` present: displace centroid (and translate bounds) along great-circle / local approximation for `forecast_minutes`.  
   - If missing velocity or direction: keep current position; reduce confidence sharply; contribute to `status=partial` when common.

2. **Intensity**  
   - If `history` has ≥ 2 intensity (or area) samples: apply a simple linear trend, clamp to a safe range (e.g. ≥ 0 and ≤ configured max).  
   - Else: keep current mean intensity (conservative fallback); do not invent growth.

3. **Rain probability**  
   - Derive a simple 0–1 score from projected intensity and confidence (deterministic heuristic). Null only if intensity truly unavailable.

4. **Confidence**  
   Start from `motion.confidence` (or a low default if absent). Multiply / subtract for:
   - longer horizons  
   - short history / `NEW`  
   - missing or unstable speed/bearing  
   - stale radar / few `frames_used`  
   - rapid change in area/intensity when detectable  
   Clamp to `[0, 1]`.

5. **Empty / failed track**  
   - No cells → `predictions=[]` with clear `message`; prefer `status=unavailable` or `ok` with empty list + message (pick one consistently in implementation: **`unavailable` when track unavailable; `ok` with empty predictions when track succeeded but no active cells**).  
   - Track `unavailable` → nowcast `unavailable`.  
   - Never fabricate cells.

`LOST` / `EXPIRED` cells are not projected as active forecasts (omit or only surface if needed for debugging — default: **omit**).

## 7. API

| Method | Path | Body |
|---|---|---|
| POST | `/api/nowcasting/predict` | `NowcastPredictRequest` |

- Register router in `main.py` similarly to rain-cells (prefer try/except isolation so Stage 5 load failure does not take down Stage 1–2).  
- Reuse rain-cell buffer defaults from settings when `buffer_km` omitted.  
- Errors follow existing patterns (`503` / `502` where appropriate for upstream failure).

Do **not** overload `POST /api/rain-cells/track` with predictions.

## 8. Frontend Integration

### Toggle & timeline

- Add **Nowcasting** toggle to `RadarControls` (same interaction language as Rain cells / Radar / Satellite).  
- When enabled and route geometry exists, `useNowcasting` calls the predict API.  
- Show timeline:

```text
NOW ── +5m ── +10m ── +15m ── +30m ── +60m
```

- `NOW`: observed layers only (existing radar / rain cells behavior).  
- Selected horizon ≠ `NOW`: show predicted layers for that horizon.

### Map layers

Distinct from observed rain-cell styling (e.g. dashed bounds, different hue such as teal/cyan, lower fill opacity, horizon label). Include a legend/badge: **Predicted — Baseline v0.1**.

### Info panel

On selecting a predicted cell, show forecast minutes, rain probability, predicted intensity, confidence, movement (bearing + speed), and model name/version, plus a short disclaimer that data is predicted.

### Composable

`useNowcasting`: `enabled`, `selectedHorizon`, loading/error, response cache; refresh on route change and a polite interval (same order of magnitude as rain cells, ~5 minutes). Do not recompute predictions on every map render.

Do not redesign Stage 1 `WeatherTimeline` (route ETA forecast cards).

## 9. Missing / Stale Data Handling

| Situation | Behavior |
|---|---|
| No active rain cells | Empty predictions + clear message |
| Missing velocity / direction | Hold position; low confidence; often `partial` |
| Insufficient history | Conservative intensity; lower confidence |
| Stale radar / few frames | Lower confidence; may be `partial` |
| Unstable motion | Lower confidence |
| Track service unavailable | `status=unavailable` |
| Missing satellite / forecast | Irrelevant to Stage 5 path (cell-only input); ignore |

Never invent sensor observations.

## 10. Performance

- Prediction runs in backend service/engine, not in Vue render loops.  
- Reuse Stage 3 tracking results within the same request (single track call inside `NowcastingService`).  
- Optional light response caching only if it matches existing project patterns; do not add new infrastructure (Redis, etc.) in Stage 5.

## 11. Testing

Minimum backend coverage:

1. Horizon generation (5/10/15/30/60)  
2. Position projection with known speed/bearing  
3. Missing velocity handling  
4. Missing direction handling  
5. Intensity extrapolation with history vs fallback  
6. Confidence decreases with horizon  
7. Short history / NEW cell  
8. Stale / low `frames_used`  
9. No rain-cell scenario  
10. Normalized prediction fields (`kind`, model info, geometry)  
11. API response structure (schema / endpoint with mocked service)

Include realistic edge cases (zero speed, opposite bearing wrap, empty geometry rejected by validation).

## 12. Documentation & Delivery

- This design file is the Stage 5 architecture source of truth.  
- README roadmap: mark Stage 5 in progress / done when implementation lands.  
- Implementation plan follows after this spec is user-reviewed.

## 13. Out of Scope / Non-goals

- Rewriting Stage 1–4  
- Second rain-cell tracker  
- Training neural networks / large ML pipelines  
- Claiming calibrated scientific accuracy  
- Microservices split  
- New dashboards beyond toggle + timeline + panel  
- Fake historical training data  
- Binding nowcast into route risk scoring / ETA (future stage)

## 14. Acceptance Criteria

Stage 5 is complete when:

- [ ] Stage 1–4 behavior still works with nowcasting off  
- [ ] Modular `NowcastingEngine` + `NowcastingModel` interface exist  
- [ ] `BaselineExtrapolationModel` (`baseline` / `0.1`) exists  
- [ ] Tracked cells project to 5/10/15/30/60 minutes with geometry  
- [ ] Predictions include probability/intensity/confidence and `kind=predicted`  
- [ ] `POST /api/nowcasting/predict` returns normalized response  
- [ ] Frontend toggle + timeline update map by horizon  
- [ ] Predicted cells are inspectable and visually distinct from observations  
- [ ] Missing/stale data handled without fabrication  
- [ ] Core prediction logic has tests  
- [ ] Architecture documents where a real ML model plugs in later  

## 15. Files Likely Touched (implementation preview)

**Backend (new):**  
`schemas/nowcasting.py`, `engine/nowcasting_models.py` (protocol + baseline), `engine/nowcasting_engine.py`, `services/nowcasting_service.py`, `api/nowcasting.py`, `tests/test_nowcasting*.py`

**Backend (modify):**  
`main.py` (router registration), possibly `config.py` for horizons / model name defaults

**Frontend (new/modify):**  
`composables/useNowcasting.ts`, `types/nowcasting.ts`, `RadarControls.vue`, `RouteMap.vue`, `pages/index.vue`, small utils for predicted GeoJSON

**Docs:**  
this spec; README Stage 5 note

## 16. Known Limitations (accepted)

- Baseline advection only; no convective initiation/decay physics beyond simple intensity trend  
- Growth/decay from short RainViewer history is weak  
- Confidence is heuristic, not probability-calibrated  
- Corridor / route-scoped cells only — not full-domain nowcasting  
- Visual prediction ≠ meteorological verification product

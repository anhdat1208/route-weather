# Route Weather Stage 1 MVP — Design Specification

> Approved: 2026-08-21  
> Approach: **Harden-in-place** on existing Nuxt 4 + FastAPI monorepo  
> Supersedes scope emphasis of `2026-08-19-route-weather-design.md` for Stage 1 UI surface (risk/compare hidden). Engine/API risk remains for later stages.

## 1. Product Goal

Answer: *"If I travel from A to B, what weather conditions am I likely to encounter along the route and at what time?"*

Combine route geometry, travel ETA, weather along sampled points, and a weather timeline. No radar, satellite, rain-cell tracking, ML/AI nowcasting, or traffic prediction in Stage 1.

## 2. Decisions Locked

| Topic | Decision |
|---|---|
| Strategy | Align & harden existing codebase; do not rewrite |
| Risk / Compare UI | Hide from main UI; keep engine + API fields |
| Sampling | Distance interval + min/max clamp |
| Form fields | Origin, destination, travel mode, departure time |
| Frontend split | Moderate: RouteForm, RouteMap, JourneySummary, WeatherTimeline + composable |
| Implementation style | Harden-in-place (approach 1) |

## 3. External Services

| Service | Role | Key |
|---|---|---|
| GraphHopper Cloud | Routing + geocoding | `GRAPHHOPPER_API_KEY` |
| Open-Meteo | Weather forecast | None |
| OpenFreeMap / MapLibre | Map tiles | None |

Never hard-code secrets. Document all env vars in `.env.example` and README.

## 4. System Architecture

```text
User → RouteForm
         ↓
  useRouteWeather (composable)
         ↓
  POST /api/route-weather
         ↓
  RouteWeatherEngine
   ├── RouteProvider (GraphHopper)
   ├── GeocodeProvider (GraphHopper)
   ├── Sampler (interval km + min/max)
   ├── ETA
   └── WeatherProvider (Open-Meteo) → WeatherSnapshot
         ↓
  RouteMap + JourneySummary + WeatherTimeline
```

**Rules:**
- Backend owns business logic; frontend renders pre-computed results.
- UI must not depend on raw third-party weather response shapes.
- Flow: External API → Weather Adapter/Provider → Internal model → UI.
- Map component must allow future layers without rewrite:

```text
Map
 ├── Base Map
 ├── Route Layer
 ├── Weather Point Layer
 ├── [Future] Radar Layer
 ├── [Future] Satellite Layer
 ├── [Future] Rain Cell Layer
 └── [Future] Traffic Layer
```

## 5. Sampling Strategy

Config (environment):

| Variable | Purpose | Example default |
|---|---|---|
| `ROUTE_WEATHER_SAMPLE_INTERVAL_KM` | Target spacing between sample points | `10` |
| `ROUTE_WEATHER_MIN_POINTS` | Floor on sample count | `5` |
| `ROUTE_WEATHER_MAX_POINTS` | Cap to avoid request explosion | `20` |

Algorithm:

1. Measure route length from geometry.
2. `count ≈ round(distance_km / interval_km) + 1` (include endpoints).
3. Clamp to `[MIN_POINTS, MAX_POINTS]`.
4. Place points evenly by cumulative distance; always include origin and destination.
5. Fetch weather only for sampled points — never for every coordinate in the polyline.

## 6. Internal Weather Model

Keep / align with existing normalized snapshot (Python Pydantic / TS mirror):

```typescript
interface RouteWeatherPoint {
  latitude: number
  longitude: number
  estimatedArrivalTime: string
  temperature?: number
  feelsLike?: number
  precipitationProbability?: number
  precipitation?: number
  humidity?: number
  windSpeed?: number
  windDirection?: number
  weatherCode?: number
  weatherDescription?: string
  source?: string
}
```

Backend already uses `WeatherSnapshot` / timeline points — map fields consistently; do not expose Open-Meteo raw JSON to the UI.

## 7. API Surface (Stage 1)

Primary:

- `POST /api/route-weather` — route + sampled weather timeline
- `GET /api/geocode` — autocomplete
- `GET /api/health` — health

Retain (backend only / unused by Stage 1 UI):

- Risk fields on response
- Recommendation / alternatives
- `POST /api/route-weather/compare` if already present

Stage 1 UI ignores risk and compare payloads.

## 8. Frontend Structure

Split monolithic `frontend/app/pages/index.vue` into:

| Module | Responsibility |
|---|---|
| `components/RouteForm.vue` | Origin/dest autocomplete, mode, departure, CTA, form errors |
| `components/JourneySummary.vue` | Distance, duration, departure display, ETA |
| `components/RouteMap.vue` | MapLibre: base, route polyline, origin/dest markers, weather point markers; layer stubs for future |
| `components/WeatherTimeline.vue` | Scrollable timeline: time, location, condition, temp, rain %, precip when available |
| `composables/useRouteWeather.ts` | API calls, loading phases, error handling |
| `types/routeWeather.ts` | Client types for normalized response |

**UI layout:**

```text
------------------------------------------------
| Route Weather                                |
------------------------------------------------
| From / To / Mode / Departure / Analyze       |
------------------------------------------------
| Journey Summary (distance, ETA)              |
------------------------------------------------
| MAP (primary)                                |
------------------------------------------------
| Weather Along Your Route (timeline)          |
------------------------------------------------
```

**Hidden from UI:** risk gauge, recommendation card, compare tab, risk-colored legend/bar, worst-segment risk highlighting.

**Loading copy (VI or equivalent):**
- Calculating route…
- Analyzing weather along your journey…

## 9. Error Handling

| Case | Behavior |
|---|---|
| Invalid origin | Clear message; app remains usable |
| Invalid destination | Clear message; app remains usable |
| Route not found | User-friendly route error |
| Full weather API failure | Route still shown; banner that weather is temporarily unavailable |
| Partial weather failure | Failed points show unavailable/`—`; do not discard whole route |

Never crash the app on a single weather point failure. Never invent fake weather values.

## 10. Testing & Verification

After implementation:

1. Run existing backend test suite.
2. Run lint / typecheck if available.
3. Build frontend.
4. Smoke scenarios:
   - Valid A→B: route, distance, ETA, weather points, timeline
   - Invalid location: friendly error
   - Weather failure: route works, weather degraded gracefully
   - Long route: sample count capped; no request explosion

## 11. Documentation

Update root `README.md`:

- Project purpose
- Stage 1 scope
- Architecture overview
- Setup + env vars (including sample interval)
- How route-weather calculation works
- How to run
- Known limitations
- Roadmap:

```text
## Roadmap

[x] Stage 1 — Route Weather MVP
[ ] Stage 2 — Live Radar
[ ] Stage 3 — Rain-cell Tracking
[ ] Stage 4 — Satellite + Data Fusion
[ ] Stage 5 — AI Nowcasting
[ ] Stage 6 — Traffic Prediction
[ ] Stage 7 — Route Weather Intelligence
```

## 12. Out of Scope (Hard)

- Radar tiles / animated rain
- Satellite layers
- Rain-cell polygons / tracking
- ML / Gemini / LLM prediction
- Traffic prediction / heatmaps
- Expanding risk scoring UX in Stage 1
- Unrelated refactors or dependency churn

## 13. Definition of Done

- [ ] User can enter origin and destination (plus mode + departure)
- [ ] Route calculated and shown on map
- [ ] Distance and duration displayed
- [ ] Configurable sampling (interval + min/max)
- [ ] Weather associated with sampled points + ETA
- [ ] Weather timeline displayed
- [ ] Map and timeline conceptually aligned
- [ ] Loading and error states present
- [ ] Weather normalized via adapter/provider
- [ ] Secrets via environment variables
- [ ] No radar/satellite/AI/traffic implemented
- [ ] Tests / typecheck / lint / build pass as available
- [ ] README updated with roadmap
- [ ] Architecture ready for Stage 2 map layers

## 14. Known Limitations (carry forward)

- Open-Meteo hourly resolution
- GraphHopper free tier limits / non-commercial
- No traffic-aware ETA
- Geocoding accuracy varies for small Vietnamese streets
- Forecasts are probabilistic

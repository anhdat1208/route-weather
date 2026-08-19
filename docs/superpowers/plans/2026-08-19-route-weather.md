# Route Weather MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-quality MVP that maps weather forecasts onto travel routes in space and time.

**Architecture:** Monorepo with Nuxt 4 frontend, FastAPI backend, PostgreSQL cache. Provider abstractions for routing (GraphHopper), weather (Open-Meteo), geocoding (GraphHopper). Route Weather Engine handles sampling, ETA, risk calculation.

**Tech Stack:** Nuxt 4, Vue 3, TypeScript, Tailwind CSS, Pinia, MapLibre GL JS, Python, FastAPI, PostgreSQL, Docker Compose

## Global Constraints

- No Local Rain, radar, satellite, or AI features
- No fake/placeholder weather data — real providers only
- GraphHopper free tier (500 credits/day, non-commercial)
- Open-Meteo for weather (no key)
- OpenFreeMap for map tiles (no key)
- Vietnamese UI text matching approved mockup
- Dark mode default, UI per mockup design spec
- TypeScript strict mode, typed API contracts
- Core engine heavily unit-tested

---

### Task 1: Project Scaffold

**Files:**
- Create: `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`
- Create: `backend/Dockerfile`, `backend/requirements.txt`, `backend/app/main.py`, `backend/app/config.py`
- Create: `frontend/` via `npx nuxi@latest init`

- [ ] **Step 1:** Init git repo, create `.gitignore`
- [ ] **Step 2:** Create `docker-compose.yml` with db, backend, frontend services
- [ ] **Step 3:** Create FastAPI skeleton with `/api/health` endpoint
- [ ] **Step 4:** Init Nuxt 4 with Tailwind, Pinia, VueUse
- [ ] **Step 5:** Verify `docker compose up` starts all services

### Task 2: Provider Abstractions + GraphHopper

**Files:**
- Create: `backend/app/providers/base.py`, `backend/app/providers/graphhopper.py`
- Create: `backend/app/schemas/` (request/response types)
- Test: `backend/tests/test_graphhopper.py`

- [ ] **Step 1:** Define Protocol classes for GeocodeProvider, RouteProvider
- [ ] **Step 2:** Implement GraphHopperGeocodeProvider (search + reverse)
- [ ] **Step 3:** Implement GraphHopperRouteProvider (motorcycle + foot profiles)
- [ ] **Step 4:** Write integration test with real API (skip if no key)
- [ ] **Step 5:** Create GeocodeService and RouteService wrappers

### Task 3: Route Sampling + ETA

**Files:**
- Create: `backend/app/engine/sampler.py`, `backend/app/engine/eta.py`
- Test: `backend/tests/test_sampler.py`, `backend/tests/test_eta.py`

- [ ] **Step 1:** Write failing tests for sampler (point count by distance, origin/dest included)
- [ ] **Step 2:** Implement Douglas-Peucker simplification + distance-based sampling
- [ ] **Step 3:** Write failing tests for ETA (proportional calculation, different departure times)
- [ ] **Step 4:** Implement ETA calculator
- [ ] **Step 5:** All tests pass

### Task 4: Open-Meteo Weather + Cache

**Files:**
- Create: `backend/app/providers/open_meteo.py`, `backend/app/cache/postgres_cache.py`
- Create: `backend/app/db/migrations/001_cache.sql`
- Test: `backend/tests/test_weather.py`, `backend/tests/test_cache.py`

- [ ] **Step 1:** Define WeatherProvider protocol + WeatherForecast schema
- [ ] **Step 2:** Implement OpenMeteoProvider with hourly forecast lookup
- [ ] **Step 3:** Implement batch forecast method
- [ ] **Step 4:** Create PostgreSQL cache table + cache service with TTL
- [ ] **Step 5:** Wire WeatherService with cache layer

### Task 5: Risk Calculation + Route Weather Engine

**Files:**
- Create: `backend/app/engine/risk.py`, `backend/app/engine/route_weather_engine.py`
- Test: `backend/tests/test_risk.py`, `backend/tests/test_engine.py`

- [ ] **Step 1:** Write failing tests for risk formula + precipitation classification
- [ ] **Step 2:** Implement risk calculator with configurable thresholds
- [ ] **Step 3:** Write failing test: same route, different departure → different risk
- [ ] **Step 4:** Implement RouteWeatherEngine orchestrating all services
- [ ] **Step 5:** Implement departure time comparison + recommendation generator

### Task 6: Backend API Endpoints

**Files:**
- Create: `backend/app/api/route_weather.py`, `backend/app/api/geocode.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1:** `POST /api/route-weather` with Pydantic validation
- [ ] **Step 2:** `POST /api/route-weather/compare` for departure time comparison
- [ ] **Step 3:** `GET /api/geocode` for autocomplete
- [ ] **Step 4:** Error handling middleware (provider failures, validation)
- [ ] **Step 5:** CORS config for frontend

### Task 7: Frontend — Layout + Route Form (Mockup UI)

**Files:**
- Create: `frontend/app/pages/index.vue`
- Create: `frontend/app/components/RouteForm.vue`, `JourneySummary.vue`
- Create: `frontend/app/assets/css/main.css` (dark theme tokens)
- Create: `frontend/app/types/routeWeather.ts`

- [ ] **Step 1:** Setup dark theme CSS variables matching mockup palette
- [ ] **Step 2:** Build sidebar layout with logo + tagline
- [ ] **Step 3:** Build RouteForm with autocomplete (calls `/api/geocode`)
- [ ] **Step 4:** Build JourneySummary card
- [ ] **Step 5:** Wire Pinia store + API composable

### Task 8: Frontend — Map + Route Coloring

**Files:**
- Create: `frontend/app/components/RouteMap.vue`
- Create: `frontend/app/composables/useMapLibre.ts`

- [ ] **Step 1:** Integrate MapLibre GL JS with OpenFreeMap dark style
- [ ] **Step 2:** Render route as multi-colored segments by risk level
- [ ] **Step 3:** Add origin/destination markers
- [ ] **Step 4:** Add map legend, zoom controls, fit-route button
- [ ] **Step 5:** Segment click → popup with weather details

### Task 9: Frontend — Risk Gauge + Timeline

**Files:**
- Create: `frontend/app/components/RiskGauge.vue`, `WeatherTimeline.vue`, `RecommendationCard.vue`

- [ ] **Step 1:** Build circular RiskGauge component (score/100)
- [ ] **Step 2:** Build horizontal WeatherTimeline stepper per mockup
- [ ] **Step 3:** Highlight highest-risk point with red box
- [ ] **Step 4:** Distance scale bar below timeline
- [ ] **Step 5:** Info banner for worst segment + RecommendationCard

### Task 10: Frontend — Tabs + Departure Comparison

**Files:**
- Create: `frontend/app/components/DepartureComparison.vue`
- Modify: `frontend/app/pages/index.vue`

- [ ] **Step 1:** Tab bar: Bản đồ | Timeline | So sánh thời gian
- [ ] **Step 2:** DepartureComparison view with risk scores per time
- [ ] **Step 3:** Dark/Light mode toggle
- [ ] **Step 4:** Connect all tabs to Pinia store state

### Task 11: Mobile Responsive

**Files:**
- Modify: layout components for mobile breakpoints

- [ ] **Step 1:** Map full-screen on mobile
- [ ] **Step 2:** Bottom sheet for form/summary/timeline
- [ ] **Step 3:** Swipeable sheet states
- [ ] **Step 4:** Test on mobile viewport

### Task 12: Testing + Polish

- [ ] **Step 1:** Run full backend test suite
- [ ] **Step 2:** Manual E2E test: Chánh Hưng → Tây Thạnh, motorbike, 15:30
- [ ] **Step 3:** Verify route coloring, timeline, risk score, recommendation
- [ ] **Step 4:** Error state UI (no weather, no route, invalid address)
- [ ] **Step 5:** Accessibility: keyboard nav, screen reader labels, focus states

### Task 13: Documentation + Deployment

- [ ] **Step 1:** Complete README with local dev instructions
- [ ] **Step 2:** Document all env vars
- [ ] **Step 3:** Production deployment guide (Docker)
- [ ] **Step 4:** Final architecture summary

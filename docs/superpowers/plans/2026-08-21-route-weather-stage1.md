# Stage 1 Route Weather Harden-in-place Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the existing Nuxt 4 + FastAPI Route Weather MVP so Stage 1 DoD is met: configurable interval sampling, graceful weather failures, lean UI (route + timeline, risk/compare hidden), modular frontend, updated docs.

**Architecture:** Keep backend as source of truth (GraphHopper + Open-Meteo → RouteWeatherEngine → normalized response). Change primary `/api/route-weather` to a single `compute()` (stop triple-compare on every analyze). Frontend splits into form/map/summary/timeline + composable; map uses Base/Route/WeatherPoints layers.

**Tech Stack:** Python 3.12, FastAPI, Pydantic Settings, httpx, pytest; Nuxt 4, Vue 3, TypeScript, MapLibre GL, Tailwind, VueUse.

## Global Constraints

- Harden-in-place only — no rewrite, no new major dependencies.
- No radar / satellite / rain-cell / ML / AI / traffic features.
- Risk + compare remain in API/engine; **hidden from Stage 1 UI**.
- Secrets only via env vars; update `.env.example`.
- Sampling: `ROUTE_WEATHER_SAMPLE_INTERVAL_KM` + existing min/max clamp.
- UI language: Vietnamese.
- Git on this machine may fail `git commit` with `unknown option trailer` (Git 2.27 + wrapper). If commit fails, stage files and continue; do not spend time fighting git config.
- Spec: `docs/superpowers/specs/2026-08-21-route-weather-stage1-design.md`

## File Structure

| Path | Responsibility |
|---|---|
| `backend/app/config.py` | Add `route_weather_sample_interval_km` |
| `.env.example` | Document new env var |
| `backend/app/engine/sampler.py` | Interval-based `decide_sample_count` |
| `backend/tests/test_sampler.py` | Tests for interval + clamp |
| `backend/app/schemas/route_weather.py` | Optional weather; `weather_status` |
| `backend/app/engine/route_weather_engine.py` | Partial weather failure handling |
| `backend/app/api/route_weather.py` | Primary endpoint = single `compute()` |
| `backend/tests/test_engine.py` | Partial failure + single-compute behavior |
| `frontend/app/types/routeWeather.ts` | Client normalized types |
| `frontend/app/composables/useRouteWeather.ts` | API, loading phases, errors |
| `frontend/app/components/RouteForm.vue` | Inputs + autocomplete + CTA |
| `frontend/app/components/JourneySummary.vue` | Distance / duration / times |
| `frontend/app/components/WeatherTimeline.vue` | Horizontal weather timeline |
| `frontend/app/components/RouteMap.vue` | MapLibre layered map |
| `frontend/app/pages/index.vue` | Compose layout; hide risk/compare |
| `README.md` | Stage 1 docs + roadmap |

---

### Task 1: Interval sampling config + sampler

**Files:**
- Modify: `backend/app/config.py`
- Modify: `.env.example`
- Modify: `backend/app/engine/sampler.py`
- Modify: `backend/tests/test_sampler.py`

**Interfaces:**
- Consumes: existing `sample_points_by_distance(geometry, min_points=, max_points=)`
- Produces: `Settings.route_weather_sample_interval_km: float` (default `10.0`); `decide_sample_count(distance_km, interval_km=None) -> int` using `round(distance_km / interval_km) + 1` then clamp later in `sample_points_by_distance`

- [ ] **Step 1: Rewrite sampler tests for interval strategy**

Replace contents of `backend/tests/test_sampler.py` with:

```python
from __future__ import annotations

from app.config import settings
from app.engine.sampler import decide_sample_count, sample_points_by_distance
from app.schemas.common import LatLng


def test_decide_sample_count_uses_interval():
    # 25 km / 10 km → round(2.5)+1 = 4
    assert decide_sample_count(25.0, interval_km=10.0) == 4
    # 100 km / 10 → 11
    assert decide_sample_count(100.0, interval_km=10.0) == 11
    # tiny route still returns at least 2 before clamp (endpoints)
    assert decide_sample_count(1.0, interval_km=10.0) == 2


def test_sample_points_respects_min_max(monkeypatch):
    monkeypatch.setattr(settings, "route_weather_sample_interval_km", 10.0)
    monkeypatch.setattr(settings, "route_weather_min_points", 5)
    monkeypatch.setattr(settings, "route_weather_max_points", 20)

    # ~3.3 km → raw count 2, clamped to min 5
    short = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.03, lng=106.0)]
    assert len(sample_points_by_distance(short)) == 5
    assert abs(sample_points_by_distance(short)[0].point.lat - 10.0) < 1e-9
    assert abs(sample_points_by_distance(short)[-1].point.lat - 10.03) < 1e-9

    # ~66 km → round(6.6)+1=8, within [5,20]
    long_geo = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.60, lng=106.0)]
    assert len(sample_points_by_distance(long_geo)) == 8


def test_sample_points_caps_at_max(monkeypatch):
    monkeypatch.setattr(settings, "route_weather_sample_interval_km", 1.0)
    monkeypatch.setattr(settings, "route_weather_min_points", 5)
    monkeypatch.setattr(settings, "route_weather_max_points", 20)
    # ~66 km / 1 km → 67 raw, capped at 20
    geometry = [LatLng(lat=10.0, lng=106.0), LatLng(lat=10.60, lng=106.0)]
    assert len(sample_points_by_distance(geometry)) == 20
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `cd backend && python -m pytest tests/test_sampler.py -v`

Expected: FAIL (old `decide_sample_count` signature / counts)

- [ ] **Step 3: Add config + update sampler**

In `backend/app/config.py`, inside `Settings`, after `route_weather_min_points`:

```python
    route_weather_sample_interval_km: float = 10.0
```

In `.env.example`, under Route Weather Engine:

```text
ROUTE_WEATHER_SAMPLE_INTERVAL_KM=10
ROUTE_WEATHER_MAX_POINTS=20
ROUTE_WEATHER_MIN_POINTS=5
```

Replace `decide_sample_count` and keep `sample_points_by_distance` clamp logic in `backend/app/engine/sampler.py`:

```python
def decide_sample_count(distance_km: float, interval_km: float | None = None) -> int:
    """Point count from spacing interval; always at least 2 (origin + destination)."""
    interval = settings.route_weather_sample_interval_km if interval_km is None else interval_km
    if interval <= 0:
        raise ValueError("interval_km must be > 0")
    raw = int(round(distance_km / interval)) + 1
    return max(2, raw)


def sample_points_by_distance(
    geometry: list[LatLng],
    *,
    min_points: int | None = None,
    max_points: int | None = None,
    interval_km: float | None = None,
) -> list[SamplePoint]:
    if len(geometry) < 2:
        raise ValueError("Route geometry must include at least origin and destination.")

    cum = cumulative_distances_m(geometry)
    total_m = cum[-1]
    distance_km = total_m / 1000.0

    min_points = settings.route_weather_min_points if min_points is None else min_points
    max_points = settings.route_weather_max_points if max_points is None else max_points

    count = decide_sample_count(distance_km, interval_km=interval_km)
    count = max(min_points, min(max_points, count))

    samples: list[SamplePoint] = []
    for i in range(count):
        frac = 0.0 if count == 1 else i / (count - 1)
        target_m = total_m * frac
        p = find_point_at_distance_m(geometry, cum, target_m)
        samples.append(SamplePoint(index=i, point=p, distance_m=target_m))

    return samples
```

- [ ] **Step 4: Run sampler tests — expect PASS**

Run: `cd backend && python -m pytest tests/test_sampler.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/engine/sampler.py backend/tests/test_sampler.py .env.example
git commit -m "feat: sample route weather by configurable interval km"
```

---

### Task 2: Weather status schema + partial failure in engine

**Files:**
- Modify: `backend/app/schemas/route_weather.py`
- Modify: `backend/app/engine/route_weather_engine.py`
- Modify: `backend/tests/test_engine.py`

**Interfaces:**
- Consumes: `WeatherProvider.get_forecast_at`, `sample_points_by_distance`, `compute_eta`
- Produces: `RouteWeatherResponse.weather_status: Literal["ok","partial","unavailable"]`; `RouteWeatherTimelinePoint.weather: WeatherSnapshot | None`; `RouteWeatherSegment.weather: WeatherSnapshot | None`

- [ ] **Step 1: Add failing engine tests for partial weather**

Append to `backend/tests/test_engine.py`:

```python
from app.providers.errors import WeatherNotAvailableError


class FlakyWeatherProvider(WeatherProvider):
    def __init__(self, fail_indices: set[int]):
        self.fail_indices = fail_indices
        self.calls = 0

    async def get_forecast_at(self, *, lat: float, lng: float, time: datetime) -> WeatherSnapshot:
        idx = self.calls
        self.calls += 1
        if idx in self.fail_indices:
            raise WeatherNotAvailableError("simulated point failure")
        return WeatherSnapshot(
            time=time,
            precipitation_probability_pct=20,
            precipitation_mm=0,
            temperature_c=30,
            condition="Mây nhẹ",
        )


class AlwaysFailWeatherProvider(WeatherProvider):
    async def get_forecast_at(self, *, lat: float, lng: float, time: datetime) -> WeatherSnapshot:
        raise WeatherNotAvailableError("all down")


async def test_engine_partial_weather_failure_keeps_route():
    weather = FlakyWeatherProvider(fail_indices={1})
    engine = RouteWeatherEngine(
        route_provider=MockRouteProvider(),
        weather_provider=weather,
        geocode_provider=None,
    )
    result = await _compute(engine, datetime(2026, 8, 19, 15, 0, 0))
    assert result.route["distance_km"] > 0
    assert result.weather_status == "partial"
    assert any(p.weather is None for p in result.timeline)
    assert any(p.weather is not None for p in result.timeline)


async def test_engine_full_weather_failure_still_returns_route():
    engine = RouteWeatherEngine(
        route_provider=MockRouteProvider(),
        weather_provider=AlwaysFailWeatherProvider(),
        geocode_provider=None,
    )
    result = await _compute(engine, datetime(2026, 8, 19, 15, 0, 0))
    assert result.route["distance_km"] > 0
    assert result.weather_status == "unavailable"
    assert all(p.weather is None for p in result.timeline)
```

- [ ] **Step 2: Run new tests — expect FAIL**

Run: `cd backend && python -m pytest tests/test_engine.py::test_engine_partial_weather_failure_keeps_route tests/test_engine.py::test_engine_full_weather_failure_still_returns_route -v`

Expected: FAIL (AttributeError / exception raised)

- [ ] **Step 3: Update schema**

In `backend/app/schemas/route_weather.py`:

1. Add: `WeatherStatus = Literal["ok", "partial", "unavailable"]`
2. Change `RouteWeatherSegment.weather` to `WeatherSnapshot | None = None`
3. Change `RouteWeatherTimelinePoint.weather` to `WeatherSnapshot | None = None`
4. Add to `RouteWeatherResponse`:

```python
    weather_status: WeatherStatus = "ok"
```

- [ ] **Step 4: Update engine weather gather**

In `backend/app/engine/route_weather_engine.py`, replace the weather gather + risk/timeline construction so that:

1. `weather_snaps = await asyncio.gather(*weather_tasks, return_exceptions=True)`
2. Normalize each item: if `BaseException` → `None`, else snapshot
3. `ok_count = sum(1 for s in weather_snaps if s is not None)`
4. `weather_status = "ok" if ok_count == len(weather_snaps) else ("unavailable" if ok_count == 0 else "partial")`
5. For risk: use `compute_risk_score(snap)` only when snap is not None; otherwise score `0.0`
6. Timeline/segments set `weather=snap` (may be `None`)
7. Return `weather_status=weather_status` on `RouteWeatherResponse`
8. Do **not** re-raise `WeatherNotAvailableError` from per-point failures inside `_compute_from_route`

Keep existing risk/recommendation fields populated (Stage 1 UI ignores them).

- [ ] **Step 5: Run engine tests — expect PASS**

Run: `cd backend && python -m pytest tests/test_engine.py -v`

Expected: PASS (including existing risk-change test)

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/route_weather.py backend/app/engine/route_weather_engine.py backend/tests/test_engine.py
git commit -m "fix: keep route when weather points partially fail"
```

---

### Task 3: Primary API = single compute (no hidden triple compare)

**Files:**
- Modify: `backend/app/api/route_weather.py`

**Interfaces:**
- Consumes: `RouteWeatherEngine.compute(request) -> RouteWeatherResponse`
- Produces: `POST /api/route-weather` returns one compute; compare stays on `/api/route-weather/compare`

- [ ] **Step 1: Change `route_weather` handler**

Replace the try-body of `route_weather` in `backend/app/api/route_weather.py` so it calls `engine.compute(request)` once and returns it (leave recommendation as engine default). Remove the `offsets = [0, 30, 60]` / `compute_departure_comparison` path from the **primary** endpoint.

Keep exception mapping. `/api/route-weather/compare` remains unchanged.

Example try-body:

```python
        route_provider = GraphHopperRouteProvider()
        weather_provider = OpenMeteoProvider()
        geocode_provider = GraphHopperGeocodeProvider() if geocode_enabled else None

        engine = RouteWeatherEngine(
            route_provider=route_provider,
            weather_provider=weather_provider,
            geocode_provider=geocode_provider,
        )
        return await engine.compute(request)
```

- [ ] **Step 2: Run API + engine tests**

Run: `cd backend && python -m pytest tests/ -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/route_weather.py
git commit -m "perf: analyze route weather with single compute"
```

---

### Task 4: Frontend types + composable

**Files:**
- Create: `frontend/app/types/routeWeather.ts`
- Create: `frontend/app/composables/useRouteWeather.ts`

**Interfaces:**
- Consumes: `POST ${apiBaseUrl}/api/route-weather`, `GET /api/geocode`, `GET /api/health`
- Produces: `useRouteWeather()` exporting health/loading/error/form/route state and `analyze()`

- [ ] **Step 1: Create `frontend/app/types/routeWeather.ts`**

```typescript
export type LatLng = { lat: number; lng: number }
export type GeocodeResult = { label: string; point: LatLng; approximate?: boolean }
export type TravelMode = "motorbike" | "walking"
export type WeatherStatus = "ok" | "partial" | "unavailable"
export type RiskLevel = "very_low" | "low" | "moderate" | "high" | "very_high"

export type WeatherSnapshot = {
  time: string
  weather_code?: number | null
  condition?: string | null
  temperature_c?: number | null
  apparent_temperature_c?: number | null
  precipitation_probability_pct?: number | null
  precipitation_mm?: number | null
  wind_speed_kmh?: number | null
  wind_direction_deg?: number | null
  humidity_percent?: number | null
  visibility_km?: number | null
}

export type RouteWeatherTimelinePoint = {
  index: number
  arrival_time: string
  distance_km: number
  label: string | null
  weather: WeatherSnapshot | null
  precipitation_probability_pct: number | null
  precipitation_label: { label: string; probability_pct: number } | null
}

export type RouteWeatherSegment = {
  index: number
  coordinates: LatLng[]
  arrival_time: string
  start_distance_km: number
  end_distance_km: number
  risk_score: number
  risk_level: RiskLevel
  weather: WeatherSnapshot | null
  label: string | null
}

export type RouteWeatherResponse = {
  route: { distance_km: number; duration_minutes: number }
  weather_status: WeatherStatus
  risk: { score: number; level: RiskLevel; summary: string; worst_segment_index: number | null }
  segments: RouteWeatherSegment[]
  timeline: RouteWeatherTimelinePoint[]
  recommendation: {
    message: string
    alternatives: Array<{ departure_time: string; risk_score: number; level: RiskLevel }>
  }
}

export type LoadingPhase = "idle" | "routing" | "weather" | "done"
```

- [ ] **Step 2: Create `frontend/app/composables/useRouteWeather.ts`**

Implement composable that:

- Holds form + `routeWeather` + `loading` + `loadingPhase` + `errorMessage` + `weatherWarning` + `healthOk`
- Debounced geocode for origin/destination via `/api/geocode`
- `analyze()` POSTs to `/api/route-weather` with selected points, labels, `departure_time` as `departureLocal + ":00"`, `travel_mode`, `geocode_route_points: true`
- Sets `weatherWarning` from `weather_status` (`unavailable` / `partial`)
- Maps API errors to Vietnamese friendly messages
- `loadingMessage`: `"Đang tính lộ trình..."` / `"Đang phân tích thời tiết trên hành trình..."`
- Exports `checkHealth`, `selectOrigin`, `selectDestination`, `analyze`, and all refs above

- [ ] **Step 3: Commit**

```bash
git add frontend/app/types/routeWeather.ts frontend/app/composables/useRouteWeather.ts
git commit -m "feat: add route weather client types and composable"
```

---

### Task 5: RouteForm + JourneySummary + WeatherTimeline components

**Files:**
- Create: `frontend/app/components/RouteForm.vue`
- Create: `frontend/app/components/JourneySummary.vue`
- Create: `frontend/app/components/WeatherTimeline.vue`

**Interfaces:**
- Consumes: props from page / composable
- Produces: presentational UI only (emits for form actions)

- [ ] **Step 1: Create `RouteForm.vue`**

Props: `originQuery`, `destinationQuery`, suggestion lists, `travelMode`, `departureLocal`, `loading`, `loadingMessage`, `errorMessage`, `weatherWarning`, `canSubmit`.

Emits: update events for queries/mode/departure, `selectOrigin`, `selectDestination`, `analyze`.

Show Vietnamese labels; CTA `"Phân tích lộ trình"`; display error + weather warning.

- [ ] **Step 2: Create `JourneySummary.vue`**

Props: `distanceKm`, `durationMinutes`, `departureDisplay`, `etaDisplay`. Title: `Tổng quan hành trình`.

- [ ] **Step 3: Create `WeatherTimeline.vue`**

Props: `points: RouteWeatherTimelinePoint[]`.

Horizontal scroll cards: time, label, icon, rain %, temp; if `weather` null show `"Thời tiết không khả dụng"`; show precip mm when present. **No risk highlighting.**

- [ ] **Step 4: Commit**

```bash
git add frontend/app/components/RouteForm.vue frontend/app/components/JourneySummary.vue frontend/app/components/WeatherTimeline.vue
git commit -m "feat: add route form, summary, and weather timeline components"
```

---

### Task 6: RouteMap with future-ready layers

**Files:**
- Create: `frontend/app/components/RouteMap.vue`

**Interfaces:**
- Consumes: `routeWeather: RouteWeatherResponse | null`
- Produces: MapLibre map with `route-line` + `weather-points` sources/layers

- [ ] **Step 1: Create `RouteMap.vue`**

1. Dynamic-import maplibre on client; style from `useRuntimeConfig().public.mapStyleUrl`.
2. Watch `routeWeather` → `renderLayers()`.
3. Single-color route line (`#38bdf8`) — **no risk coloring**.
4. Weather point circle layer from timeline positions (use segment start coords / last endpoint).
5. Green origin + red destination markers; `fitBounds`.
6. Comment stub for future layers: radar, satellite, rain-cell, traffic.

- [ ] **Step 2: Commit**

```bash
git add frontend/app/components/RouteMap.vue
git commit -m "feat: add layered RouteMap without risk coloring"
```

---

### Task 7: Wire `index.vue` Stage 1 layout (hide risk/compare)

**Files:**
- Modify: `frontend/app/pages/index.vue`

**Interfaces:**
- Consumes: `useRouteWeather`, components from Tasks 5–6
- Produces: Stage 1 UI only

- [ ] **Step 1: Replace page**

Compose sidebar: header + `RouteForm` + `JourneySummary` + API health.

Main: `ClientOnly` → `RouteMap` + `WeatherTimeline` under map.

**Remove:** risk gauge, recommendation, compare tab, risk legend, risk color bar, worst-segment captions.

- [ ] **Step 2: Build frontend**

Run: `cd frontend && npm run build`

Expected: success. Fix template/TS until green.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/pages/index.vue
git commit -m "refactor: Stage 1 UI without risk and compare surfaces"
```

---

### Task 8: README documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Include: purpose, Stage 1 scope/non-goals, architecture pipeline, setup, env vars (including `ROUTE_WEATHER_SAMPLE_INTERVAL_KM`), how sampling+ETA+weather works, run instructions, pytest command, limitations, roadmap:

```markdown
## Roadmap

- [x] Stage 1 — Route Weather MVP
- [ ] Stage 2 — Live Radar
- [ ] Stage 3 — Rain-cell Tracking
- [ ] Stage 4 — Satellite + Data Fusion
- [ ] Stage 5 — AI Nowcasting
- [ ] Stage 6 — Traffic Prediction
- [ ] Stage 7 — Route Weather Intelligence
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document Stage 1 architecture and roadmap"
```

---

### Task 9: Full verification

**Files:** none new (fix only)

- [ ] **Step 1: Backend tests**

Run: `cd backend && python -m pytest tests/ -v`

Expected: all PASS

- [ ] **Step 2: Frontend build**

Run: `cd frontend && npm run build`

Expected: success

- [ ] **Step 3: Smoke checklist for final summary**

| Scenario | Check |
|---|---|
| Valid A→B | Route on map, distance, ETA, timeline |
| Invalid location | Friendly error, UI usable |
| Weather unavailable / partial | Route remains; banner shown |
| Long route | Sample count ≤ `MAX_POINTS` |

- [ ] **Step 4: Commit fixes only if needed**

```bash
git add -A
git commit -m "fix: address Stage 1 verification issues"
```

---

## Spec coverage (self-review)

| Spec requirement | Task |
|---|---|
| Interval + min/max sampling | Task 1 |
| Normalized weather / adapter | Existing Open-Meteo provider; Task 2 nullable weather |
| Partial / full weather failure | Task 2 |
| Avoid request explosion | Task 1 + Task 3 |
| Hide risk/compare UI | Task 7 |
| Modular frontend | Tasks 4–7 |
| Layered map for Stage 2 | Task 6 |
| Loading / errors | Tasks 4–5 |
| Env + `.env.example` | Task 1 |
| README + roadmap | Task 8 |
| Tests / build | Task 9 |
| No radar/AI/traffic | Global constraints |

**Placeholder scan:** none.  
**Type consistency:** `weather_status` and optional `weather` aligned backend ↔ `frontend/app/types/routeWeather.ts`.

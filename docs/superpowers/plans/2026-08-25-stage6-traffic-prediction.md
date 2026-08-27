# Stage 6 Traffic Prediction & Weather Impact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a modular traffic layer with synthetic current traffic, baseline multi-horizon prediction, and a separate rule-based weather impact from Stage 5 nowcast, exposed via `POST /api/traffic/prediction` and visualized on the existing map.

**Architecture:** `TrafficProvider` (default `SyntheticTrafficProvider`) builds `RoadSegment`s from the route polyline. `BaselineTrafficModel` predicts base speed; `WeatherImpactModel` estimates a speed delta from nowcast rain; `TrafficPredictionEngine` combines them. Frontend `useTraffic` is independent of `useNowcasting` (separate horizon state).

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest; Nuxt 4, Vue 3, TypeScript, MapLibre GL, Tailwind.

**Spec:** `docs/superpowers/specs/2026-08-25-stage6-traffic-prediction-design.md`

## Global Constraints

- Branch: `feat/stage6-traffic-prediction` (already created from `main`; spec commit exists).
- Do **not** rewrite Stage 1–5; do **not** replace the Nowcasting Engine; do **not** duplicate rain-cell tracking.
- Default traffic is **synthetic** (`source="synthetic"`). UI must never claim live traffic.
- Model identity: `name="baseline"`, `version="0.1"`.
- Horizons fixed: `[5, 10, 15, 30]` minutes (no +60m for traffic).
- Keep **base_prediction**, **weather_impact**, and **weather-adjusted** separate in every prediction item.
- `predicted_speed_kmh` / `predicted_congestion` = weather-adjusted values used for map coloring.
- Traffic UI horizon is **independent** of nowcast `selectedHorizon`.
- UI language: Vietnamese (match existing controls).
- Git on this machine may fail `git commit` with `unknown option trailer` (Git 2.27 + wrapper). Workaround: write a msg file then `& "C:\Program Files\Git\bin\git.exe" commit -F <msgfile>`.
- No new Redis/microservices/DL training/paid traffic API in Stage 6.
- Do not build Stage 7 routing / traffic-aware ETA product.

## File Structure

| Path | Responsibility |
|---|---|
| `backend/app/config.py` | Traffic model, horizons, sample interval, impact knobs |
| `backend/app/schemas/traffic.py` | Request/response Pydantic models |
| `backend/app/engine/traffic_state.py` | Congestion / relative_speed / clamp helpers |
| `backend/app/providers/base.py` | Add `TrafficProvider` Protocol |
| `backend/app/providers/synthetic_traffic.py` | Deterministic synthetic current traffic |
| `backend/app/engine/traffic_models.py` | `TrafficPredictionModel` + `BaselineTrafficModel` |
| `backend/app/engine/weather_impact.py` | Rule-based weather impact |
| `backend/app/engine/traffic_engine.py` | Combine + confidence + status |
| `backend/app/services/traffic_service.py` | Provider + nowcast + engine |
| `backend/app/api/traffic.py` | `POST /api/traffic/prediction` |
| `backend/app/main.py` | Isolated router registration |
| `backend/tests/test_traffic_state.py` | Normalization |
| `backend/tests/test_traffic_synthetic.py` | Provider segments |
| `backend/tests/test_traffic_baseline.py` | Baseline horizons / ToD |
| `backend/tests/test_weather_impact.py` | Rain bands + dampening |
| `backend/tests/test_traffic_engine.py` | Combine, stale, missing nowcast |
| `backend/tests/test_traffic_api.py` | HTTP + mocked nowcast |
| `frontend/app/types/traffic.ts` | Client types |
| `frontend/app/composables/useTraffic.ts` | Fetch + own horizon |
| `frontend/app/utils/traffic.ts` | GeoJSON + popup + colors |
| `frontend/app/components/RadarControls.vue` | Traffic toggles + traffic timeline |
| `frontend/app/components/RouteMap.vue` | Traffic line layers + click panel |
| `frontend/app/pages/index.vue` | Wire composable |
| `README.md` | Stage 6 section |

---

### Task 1: Config, schemas, congestion helpers

**Files:**
- Modify: `backend/app/config.py`
- Create: `backend/app/schemas/traffic.py`
- Create: `backend/app/engine/traffic_state.py`
- Create: `backend/tests/test_traffic_state.py`

**Interfaces:**
- Produces:
  - Settings fields listed in Step 3
  - `congestion_from_relative(relative: float | None) -> CongestionLevel | None`
  - `relative_speed(current: float | None, free_flow: float | None) -> float | None`
  - `clamp_speed(speed: float, free_flow: float | None) -> float`
  - Schemas: `TrafficPredictRequest`, `TrafficStateOut`, `RoadSegmentOut`, `TrafficPredictionOut`, `TrafficPredictionResponse`, `WeatherImpactInfo`, `SpeedCongestionPair`, `TrafficModelInfo`

- [ ] **Step 1: Write failing congestion tests**

Create `backend/tests/test_traffic_state.py`:

```python
from __future__ import annotations

from app.engine.traffic_state import (
    clamp_speed,
    congestion_from_relative,
    relative_speed,
)


def test_relative_speed_and_none():
    assert relative_speed(40.0, 40.0) == 1.0
    assert abs(relative_speed(20.0, 40.0) - 0.5) < 1e-9
    assert relative_speed(None, 40.0) is None
    assert relative_speed(20.0, 0.0) is None


def test_congestion_bands():
    assert congestion_from_relative(0.95) == "free"
    assert congestion_from_relative(0.80) == "slow"
    assert congestion_from_relative(0.60) == "moderate"
    assert congestion_from_relative(0.40) == "heavy"
    assert congestion_from_relative(0.20) == "severe"
    assert congestion_from_relative(None) is None


def test_clamp_speed_band():
    assert clamp_speed(50.0, 40.0) == 42.0  # 1.05 * free_flow
    assert clamp_speed(2.0, 40.0) == 8.0    # 0.20 * free_flow floor
    assert clamp_speed(30.0, None) == 30.0
```

- [ ] **Step 2: Run test — expect fail**

Run: `cd backend; python -m pytest tests/test_traffic_state.py -v`  
Expected: FAIL `ImportError` / module missing

- [ ] **Step 3: Implement helpers + config + schemas**

Create `backend/app/engine/traffic_state.py`:

```python
from __future__ import annotations

from typing import Literal

CongestionLevel = Literal["free", "slow", "moderate", "heavy", "severe"]

# relative = current / free_flow
_FREE = 0.85
_SLOW = 0.70
_MODERATE = 0.50
_HEAVY = 0.30
_MAX_VS_FREE = 1.05
_MIN_VS_FREE = 0.20


def relative_speed(current: float | None, free_flow: float | None) -> float | None:
    if current is None or free_flow is None or free_flow <= 0:
        return None
    return current / free_flow


def congestion_from_relative(relative: float | None) -> CongestionLevel | None:
    if relative is None:
        return None
    if relative >= _FREE:
        return "free"
    if relative >= _SLOW:
        return "slow"
    if relative >= _MODERATE:
        return "moderate"
    if relative >= _HEAVY:
        return "heavy"
    return "severe"


def clamp_speed(speed: float, free_flow: float | None) -> float:
    if free_flow is None or free_flow <= 0:
        return max(0.0, speed)
    return max(free_flow * _MIN_VS_FREE, min(free_flow * _MAX_VS_FREE, speed))
```

Append to `Settings` in `backend/app/config.py`:

```python
    traffic_model_name: str = "baseline"
    traffic_model_version: str = "0.1"
    traffic_horizons_minutes: list[int] = [5, 10, 15, 30]
    traffic_sample_interval_km: float = 5.0
    traffic_sample_min_points: int = 3
    traffic_sample_max_points: int = 24
    traffic_free_flow_default_kmh: float = 40.0
    traffic_stale_after_seconds: int = 900
    traffic_rain_nearby_km: float = 8.0
    traffic_base_confidence: float = 0.75
```

Create `backend/app/schemas/traffic.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng

TrafficStatus = Literal["ok", "partial", "unavailable"]
NowcastEmbedStatus = Literal["ok", "partial", "unavailable", "skipped"]
CongestionLevel = Literal["free", "slow", "moderate", "heavy", "severe"]
WeatherImpactLevel = Literal["none", "low", "moderate", "high"]
RoadType = Literal["arterial", "local", "unknown"]


class TrafficPredictRequest(BaseModel):
    geometry: list[LatLng] = Field(..., min_length=2)
    buffer_km: float | None = Field(default=None, ge=1, le=300)


class TrafficModelInfo(BaseModel):
    name: str
    version: str


class TrafficStateOut(BaseModel):
    current_speed_kmh: float | None = None
    free_flow_speed_kmh: float | None = None
    congestion_level: CongestionLevel | None = None
    relative_speed: float | None = None
    timestamp: datetime
    source: str
    stale: bool = False


class RoadSegmentOut(BaseModel):
    id: str
    geometry: list[LatLng]
    road_type: str | None = None
    name: str | None = None
    traffic: TrafficStateOut | None = None


class SpeedCongestionPair(BaseModel):
    speed_kmh: float | None = None
    congestion: CongestionLevel | None = None
    speed_delta_pct: float | None = None


class WeatherImpactInfo(BaseModel):
    speed_delta_pct: float
    level: WeatherImpactLevel
    rain_probability: float | None = Field(default=None, ge=0, le=1)
    rain_intensity: float | None = None
    reasons: list[str] = Field(default_factory=list)


class TrafficPredictionOut(BaseModel):
    road_segment_id: str
    forecast_minutes: int
    predicted_speed_kmh: float | None = None
    predicted_congestion: CongestionLevel | None = None
    confidence: float = Field(..., ge=0, le=1)
    base_prediction: SpeedCongestionPair
    weather_impact: WeatherImpactInfo
    weather_adjusted: SpeedCongestionPair
    model: TrafficModelInfo


class TrafficPredictionResponse(BaseModel):
    generated_at: datetime
    status: TrafficStatus
    model: TrafficModelInfo
    horizons: list[int]
    segments: list[RoadSegmentOut]
    predictions: list[TrafficPredictionOut]
    nowcast_status: NowcastEmbedStatus
    message: str | None = None
```

- [ ] **Step 4: Re-run tests — expect pass**

Run: `cd backend; python -m pytest tests/test_traffic_state.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

Message: `feat(traffic): add schemas and congestion helpers`

---

### Task 2: TrafficProvider + SyntheticTrafficProvider

**Files:**
- Modify: `backend/app/providers/base.py`
- Create: `backend/app/providers/synthetic_traffic.py`
- Create: `backend/tests/test_traffic_synthetic.py`

**Interfaces:**
- Consumes: `sample_points_by_distance`, `TrafficStateOut`, `RoadSegmentOut`, settings
- Produces:
  - `class TrafficProvider(Protocol): def current_for_route(self, geometry: list[LatLng], *, at: datetime | None = None) -> list[RoadSegmentOut]: ...`
  - `SyntheticTrafficProvider.current_for_route(...)`

**ToD curve (lock this formula — tests depend on it):**

```text
tod_factor(hour, weekday):
  weekday 0–4 (Mon–Fri):
    hour in [7, 8] or [17, 18] → 0.70
    hour in [6, 9, 16, 19] → 0.82
    else → 0.95
  weekend:
    hour in [10, 11, 12, 17, 18] → 0.88
    else → 0.98
current = clamp(free_flow * tod_factor * (1 - 0.04 * (index % 5)), free_flow)
```

Always `source="synthetic"`, `stale=False` for freshly built snapshots. `road_type="unknown"`. `id=f"route-seg-{i}"`. Geometry = `[samples[i].point, samples[i+1].point]` (N samples → N-1 segments).

- [ ] **Step 1: Write failing synthetic tests**

```python
from __future__ import annotations

from datetime import datetime, timezone

from app.providers.synthetic_traffic import SyntheticTrafficProvider
from app.schemas.common import LatLng


GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]


def test_synthetic_builds_labeled_segments():
    segs = SyntheticTrafficProvider().current_for_route(
        GEOM, at=datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)  # Tue 08:00 UTC
    )
    assert len(segs) >= 1
    assert segs[0].id == "route-seg-0"
    assert segs[0].traffic is not None
    assert segs[0].traffic.source == "synthetic"
    assert segs[0].traffic.stale is False
    assert segs[0].traffic.congestion_level is not None
    assert len(segs[0].geometry) == 2


def test_synthetic_rush_hour_slower_than_night():
    p = SyntheticTrafficProvider()
    rush = p.current_for_route(GEOM, at=datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc))
    night = p.current_for_route(GEOM, at=datetime(2026, 8, 25, 2, 0, tzinfo=timezone.utc))
    assert rush[0].traffic.current_speed_kmh < night[0].traffic.current_speed_kmh


def test_synthetic_same_timestamp_is_deterministic():
    p = SyntheticTrafficProvider()
    at = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
    a = p.current_for_route(GEOM, at=at)
    b = p.current_for_route(GEOM, at=at)
    assert a[0].traffic.current_speed_kmh == b[0].traffic.current_speed_kmh
```

- [ ] **Step 2: Run — expect fail**

Run: `cd backend; python -m pytest tests/test_traffic_synthetic.py -v`

- [ ] **Step 3: Implement Protocol + provider**

Add to `backend/app/providers/base.py`:

```python
from datetime import datetime
from app.schemas.traffic import RoadSegmentOut

class TrafficProvider(Protocol):
    def current_for_route(
        self,
        geometry: list[LatLng],
        *,
        at: datetime | None = None,
    ) -> list[RoadSegmentOut]:
        ...
```

Create `backend/app/providers/synthetic_traffic.py` implementing `tod_factor` and `current_for_route` as specified. Use `sample_points_by_distance` with `interval_km=settings.traffic_sample_interval_km`, `min_points=settings.traffic_sample_min_points`, `max_points=settings.traffic_sample_max_points`. Fill `TrafficStateOut` via `relative_speed` + `congestion_from_relative` + `clamp_speed`. `timestamp=at` (default `datetime.now(timezone.utc)`).

- [ ] **Step 4: Tests pass**

Run: `cd backend; python -m pytest tests/test_traffic_synthetic.py tests/test_traffic_state.py -v`

- [ ] **Step 5: Commit**

Message: `feat(traffic): add synthetic traffic provider`

---

### Task 3: BaselineTrafficModel

**Files:**
- Create: `backend/app/engine/traffic_models.py`
- Create: `backend/tests/test_traffic_baseline.py`

**Interfaces:**
- Consumes: `RoadSegmentOut`, `tod_factor` (import from synthetic provider **or** extract `tod_factor` into `engine/traffic_tod.py` if needed to avoid circular imports — **prefer extract** `tod_factor` + `hour_weekday` into `backend/app/engine/traffic_tod.py` used by both synthetic provider and baseline). If Task 2 already inlined `tod_factor` in the provider, **move** it to `traffic_tod.py` in this task and update the provider import.
- Produces:
  - `class TrafficPredictionModel(Protocol): name: str; version: str; def predict_base(self, segments, *, at: datetime, horizons: list[int]) -> list[tuple[str, int, SpeedCongestionPair]]: ...`
  - `class BaselineTrafficModel` with `name="baseline"`, `version="0.1"` (read from settings)

**Algorithm (lock):**

```text
For each segment, each horizon h:
  current = traffic.current_speed_kmh  (if None: use free_flow, mark missing_current)
  free = traffic.free_flow_speed_kmh
  expected_now = clamp(free * tod_factor(at), free)     # ignore index variation
  expected_future = clamp(free * tod_factor(at + h minutes), free)
  # drift 40% of the way from current toward expected_future (no invented history)
  base_speed = clamp(current + 0.40 * (expected_future - current), free)
  speed_delta_pct = (base_speed / current) - 1   if current > 0 else 0
  congestion from relative(base_speed, free)
```

No history list in Stage 6 synthetic → do not invent trend beyond ToD drift.

- [ ] **Step 1: Write failing tests**

```python
from __future__ import annotations

from datetime import datetime, timezone

from app.engine.traffic_models import BaselineTrafficModel
from app.providers.synthetic_traffic import SyntheticTrafficProvider
from app.schemas.common import LatLng

GEOM = [LatLng(lat=10.70, lng=106.65), LatLng(lat=10.85, lng=106.80)]


def test_baseline_emits_all_horizons():
    at = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
    segs = SyntheticTrafficProvider().current_for_route(GEOM, at=at)
    model = BaselineTrafficModel()
    out = model.predict_base(segs, at=at, horizons=[5, 10, 15, 30])
    keys = {(sid, h) for sid, h, _ in out}
    assert len(segs) * 4 == len(out)
    assert (segs[0].id, 5) in keys and (segs[0].id, 30) in keys
    assert model.name == "baseline" and model.version == "0.1"


def test_baseline_speed_within_clamp():
    at = datetime(2026, 8, 25, 2, 0, tzinfo=timezone.utc)
    segs = SyntheticTrafficProvider().current_for_route(GEOM, at=at)
    pair = BaselineTrafficModel().predict_base(segs, at=at, horizons=[15])[0][2]
    free = segs[0].traffic.free_flow_speed_kmh
    assert pair.speed_kmh is not None
    assert 0.20 * free - 1e-6 <= pair.speed_kmh <= 1.05 * free + 1e-6
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement `traffic_tod.py` + `BaselineTrafficModel`**

`predict_base` return type: `list[tuple[str, int, SpeedCongestionPair]]` (segment_id, horizon, pair). Skip segments with `traffic is None`.

- [ ] **Step 4: Tests pass** (include synthetic tests still)

- [ ] **Step 5: Commit**

Message: `feat(traffic): add baseline traffic prediction model`

---

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
  < 40 → low,   base_delta = -0.07
  < 90 → moderate, base_delta = -0.15
  else → high,  base_delta = -0.25
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

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement `estimate_impact`**

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

Message: `feat(traffic): add rule-based weather impact model`

---

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
c *= max(0.35, 1.0 - 0.012 * horizon)   # 5m≈0.94, 30m≈0.64 times base
if nowcast_status not in {"ok", "skipped"} and impact.level != "none": c *= 0.75
if "low_nowcast_confidence" in reasons: c *= 0.85
if "no_history" always true in Stage 6: c *= 0.9
clamp [0, 1]
```

**Status:**

| Condition | status | nowcast_status | message |
|---|---|---|---|
| no segments | unavailable | skipped | Vietnamese: không có đoạn đường |
| some missing current speed | partial | (from nowcast) | một số đoạn thiếu tốc độ |
| nowcast unavailable | ok (base still returned) | unavailable | thời tiết dự báo không khả dụng; dùng dự báo giao thông nền |
| else | ok | nowcast.status or skipped | None |

Engine **must** still emit base predictions when nowcast is unavailable (impact 0).

- [ ] **Step 1: Write tests**
  - combine: base 28, impact −20% → 22.4 (allow float tolerance)
  - confidence lower at 30m than 5m
  - stale traffic lowers confidence
  - empty segments → unavailable
  - nowcast unavailable → predictions non-empty, impact 0, nowcast_status unavailable
  - heavy rain reduces adjusted vs base

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement `run_traffic_prediction`**

Use `BaselineTrafficModel()` and `estimate_impact`. Horizons from `settings.traffic_horizons_minutes`. Model info from settings.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

Message: `feat(traffic): add traffic prediction engine`

---

### Task 6: TrafficService + API

**Files:**
- Create: `backend/app/services/traffic_service.py`
- Create: `backend/app/api/traffic.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_traffic_api.py`

**Interfaces:**
- `TrafficService.predict_for_route(geometry, buffer_km=None)`:
  1. `segments = SyntheticTrafficProvider().current_for_route(geometry)`
  2. Try `await get_nowcasting_service().predict_for_route(geometry, buffer_km=buffer_km)`. On exception: treat as nowcast unavailable (`NowcastPredictionResponse` with status unavailable, empty predictions) — **do not** fail the whole traffic request.
  3. Return `run_traffic_prediction(segments, nowcast=..., at=now)`
- Router: `POST /api/traffic/prediction` like nowcasting
- `main.py`: isolated `try/except` include (copy nowcasting pattern, log `"Traffic router failed to load"`)

- [ ] **Step 1: Write API test with mocked traffic service** (same pattern as `test_nowcasting_predict_endpoint_with_mock_service` swapping module `_traffic_service`)

Also add a service-level test (can live in same file) that mocks `get_nowcasting_service` to raise / return unavailable and asserts traffic status still ok with empty weather impact.

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement service, API, register router**

`get_traffic_service()` singleton like nowcasting.

- [ ] **Step 4: Tests pass**

Run: `cd backend; python -m pytest tests/test_traffic_api.py tests/test_traffic_engine.py tests/test_nowcasting_api.py -v`

- [ ] **Step 5: Commit**

Message: `feat(traffic): expose POST /api/traffic/prediction`

---

### Task 7: Frontend types + `useTraffic` + GeoJSON utils

**Files:**
- Create: `frontend/app/types/traffic.ts`
- Create: `frontend/app/composables/useTraffic.ts`
- Create: `frontend/app/utils/traffic.ts`

**Interfaces:**
- Mirror backend types. `TrafficHorizon = 5 | 10 | 15 | 30`. `TrafficSelectedHorizon = 0 | TrafficHorizon`.
- `useTraffic()`: `enabled` (`useState("traffic-enabled")`), `predictionEnabled` (`useState("traffic-prediction-enabled")`), `selectedHorizon` (`useState("traffic-horizon")` default 0), `loading`, `errorMessage`, `response`, `setEnabled`, `setPredictionEnabled`, `setHorizon`, `fetchTraffic(geometry)`.
- Fetch when **either** toggle is on and geometry length ≥ 2. Endpoint `POST /api/traffic/prediction`. Refresh 300s. If `status==="unavailable"` set error from message.
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

### Task 8: RadarControls — traffic toggles + traffic timeline

**Files:**
- Modify: `frontend/app/components/RadarControls.vue`

**Interfaces:**
- New props: `trafficEnabled`, `trafficPredictionEnabled`, `trafficLoading`, `trafficError`, `trafficModelLabel`, `trafficSelectedHorizon`, `trafficSegmentCount`
- Emits: `update:trafficEnabled`, `update:trafficPredictionEnabled`, `update:trafficSelectedHorizon`
- Copy: **Giao thông**, **Dự báo giao thông**
- Timeline only when `trafficPredictionEnabled && routeReady`: `NOW +5m +10m +15m +30m` (no +60m)
- Disclaimer: `Dự báo baseline v0.1 — giao thông synthetic (không phải live)`
- Do **not** reuse nowcast `selectedHorizon` / nowcast timeline buttons

Place the two checkboxes after nowcasting block, before radar/satellite (keep weather-layer grouping readable).

- [ ] **Step 1: Extend template + props/emits**

- [ ] **Step 2: Commit**

Message: `feat(traffic): add traffic toggles and prediction horizon UI`

---

### Task 9: RouteMap traffic layers + segment popup

**Files:**
- Modify: `frontend/app/components/RouteMap.vue`

**Interfaces:**
- New props: `trafficEnabled`, `trafficPredictionEnabled`, `trafficSelectedHorizon`, `trafficSegments`, `trafficPredictionsForHorizon`, `trafficModel`
- Source/layer IDs: `traffic-line` / `traffic-line-layer` only (do not reuse route-line or nowcast IDs)
- Show current colors when `trafficEnabled && (!trafficPredictionEnabled || trafficSelectedHorizon===0)`
- Show predicted colors when `trafficPredictionEnabled && trafficSelectedHorizon>0`
- Paint: `line-color` from feature property `color`; predicted: `line-dasharray: [2, 1]`, opacity ~0.9; current: solid
- Click → popup via `formatTrafficPopup`
- Keep existing rain/nowcast/radar behavior unchanged

Follow existing `ensureSource` / watcher pattern used for nowcast layers.

- [ ] **Step 1: Implement layers + click handler**

- [ ] **Step 2: Commit**

Message: `feat(traffic): render traffic segments on map`

---

### Task 10: Wire `index.vue` + README + regression tests

**Files:**
- Modify: `frontend/app/pages/index.vue`
- Modify: `README.md`

**Wiring:**
- Import `useTraffic`
- Watch `routeGeometry` + traffic toggles → `fetchTraffic`
- `onRefreshLayers` also refreshes traffic when either toggle on
- Pass new props to `RadarControls` and `RouteMap`
- Do not change nowcast horizon wiring

**README:** new `## Stage 6 — Traffic Prediction (baseline)` with pipeline diagram from spec, `POST /api/traffic/prediction`, synthetic disclaimer, how to test. Mark roadmap `[x] Stage 6` only in this task. Link the design spec. Keep Stage 5 section intact.

- [ ] **Step 1: Wire page**

- [ ] **Step 2: Update README**

- [ ] **Step 3: Run backend regression**

Run:

```bash
cd backend
python -m pytest tests/test_traffic_state.py tests/test_traffic_synthetic.py tests/test_traffic_baseline.py tests/test_weather_impact.py tests/test_traffic_engine.py tests/test_traffic_api.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v
```

Expected: all PASS

- [ ] **Step 4: Commit**

Message: `feat(traffic): wire Stage 6 UI and document baseline traffic prediction`

---

## Spec coverage checklist (self-review)

| Spec requirement | Task |
|---|---|
| Modular TrafficProvider | 2 |
| RoadSegment from polyline | 2 |
| Synthetic labeled current traffic | 2 |
| Baseline 5/10/15/30 | 3 |
| Weather impact separate | 4 |
| Weather-adjusted combine | 5 |
| Confidence | 5 |
| Nowcast auto-invoked | 6 |
| Missing/stale/unavailable nowcast | 4, 5, 6 |
| POST /api/traffic/prediction | 6 |
| Map current vs predicted | 8, 9 |
| Independent horizons | 7, 8 |
| Segment explainability popup | 7, 9 |
| Tests listed in spec | 1–6, 10 |
| Ready for live provider / ML | Protocol + TrafficPredictionModel |
| No Stage 1–5 rewrite | All additive |
| No Stage 7 routing | Out of scope |

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-25-stage6-traffic-prediction.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints

Which approach?

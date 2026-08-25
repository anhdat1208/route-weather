# Stage 5 AI Nowcasting Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a modular backend nowcasting pipeline with a baseline rain-cell extrapolation model (`baseline` / `0.1`), expose `POST /api/nowcasting/predict`, and visualize predicted cells on the existing map with a NOW/+5m…/+60m timeline.

**Architecture:** Reuse Stage 3 `RainCellService.track_for_route` inside `NowcastingService`. `NowcastingEngine` runs a pluggable `NowcastingModel`; Stage 5 ships only `BaselineExtrapolationModel`. Frontend adds `useNowcasting` + distinct MapLibre predicted layers; Stage 1–4 layers stay unchanged when nowcasting is off.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest; Nuxt 4, Vue 3, TypeScript, MapLibre GL, Tailwind.

**Spec:** `docs/superpowers/specs/2026-08-25-stage5-ai-nowcasting-design.md`

## Global Constraints

- Branch: `feat/stage5-ai-nowcasting` (already created from `main`).
- Do **not** rewrite Stage 1–4; do **not** create a second rain-cell tracker.
- Input path: tracked rain cells only (not fusion segments).
- Model identity: `name="baseline"`, `version="0.1"` — UI must label predictions as predicted / baseline, never as live radar.
- Horizons fixed: `[5, 10, 15, 30, 60]` minutes.
- Empty track success → `status="ok"`, `predictions=[]`, clear Vietnamese `message`.
- Track `unavailable` → nowcast `status="unavailable"`.
- UI language: Vietnamese (match existing controls).
- Git on this machine may fail `git commit` with `unknown option trailer` (Git 2.27 + wrapper). Workaround: `& "C:\Program Files\Git\bin\git.exe" commit -F <msgfile>`.
- No new Redis/microservices/DL training.

## File Structure

| Path | Responsibility |
|---|---|
| `backend/app/engine/geo_math.py` | Add `destination_point(latlng, distance_km, bearing_deg)` |
| `backend/app/config.py` | Nowcast model name/version, horizons, intensity max, confidence knobs |
| `backend/app/schemas/nowcasting.py` | Request/response Pydantic models |
| `backend/app/engine/nowcasting_models.py` | `NowcastingModel` protocol + `BaselineExtrapolationModel` |
| `backend/app/engine/nowcasting_engine.py` | Orchestrate model → normalize status |
| `backend/app/services/nowcasting_service.py` | Track then predict |
| `backend/app/api/nowcasting.py` | `POST /api/nowcasting/predict` |
| `backend/app/main.py` | Register nowcasting router (isolated try/except like rain-cells) |
| `backend/tests/test_geo_math_destination.py` | destination_point tests |
| `backend/tests/test_nowcasting_baseline.py` | Baseline algorithm tests |
| `backend/tests/test_nowcasting_engine.py` | Engine status / empty / unavailable |
| `backend/tests/test_nowcasting_api.py` | HTTP endpoint with mocked service |
| `frontend/app/types/nowcasting.ts` | Client types |
| `frontend/app/composables/useNowcasting.ts` | Fetch + horizon state |
| `frontend/app/utils/nowcast.ts` | GeoJSON builders + intensity labels |
| `frontend/app/components/RadarControls.vue` | Nowcasting toggle + timeline |
| `frontend/app/components/RouteMap.vue` | Predicted layers + popup |
| `frontend/app/pages/index.vue` | Wire composable ↔ controls ↔ map |
| `README.md` | Stage 5 section + roadmap checkbox |

---

### Task 1: Geo helper + config + schemas

**Files:**
- Modify: `backend/app/engine/geo_math.py`
- Modify: `backend/app/config.py`
- Create: `backend/app/schemas/nowcasting.py`
- Create: `backend/tests/test_geo_math_destination.py`

**Interfaces:**
- Produces:
  - `destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng`
  - Settings: `nowcast_model_name: str = "baseline"`, `nowcast_model_version: str = "0.1"`, `nowcast_horizons_minutes: list[int]` default `[5,10,15,30,60]`, `nowcast_intensity_max: float = 255.0`, `nowcast_min_frames_for_full_confidence: int = 3`
  - Schemas: `NowcastPredictRequest`, `NowcastModelInfo`, `PredictedCellMotion`, `PredictedRainCell`, `NowcastPredictionResponse`

- [ ] **Step 1: Write failing destination_point test**

Create `backend/tests/test_geo_math_destination.py`:

```python
from __future__ import annotations

from app.engine.geo_math import destination_point, haversine_distance_m
from app.schemas.common import LatLng


def test_destination_point_north_1km():
    origin = LatLng(lat=10.0, lng=106.0)
    dest = destination_point(origin, distance_km=1.0, bearing_degrees=0.0)
    dist_m = haversine_distance_m(origin, dest)
    assert abs(dist_m - 1000.0) < 15.0
    assert dest.lat > origin.lat
    assert abs(dest.lng - origin.lng) < 1e-4


def test_destination_point_east_and_zero():
    origin = LatLng(lat=10.0, lng=106.0)
    east = destination_point(origin, distance_km=2.0, bearing_degrees=90.0)
    assert east.lng > origin.lng
    same = destination_point(origin, distance_km=0.0, bearing_degrees=123.0)
    assert same.lat == origin.lat and same.lng == origin.lng
```

- [ ] **Step 2: Run test — expect fail**

Run: `cd backend; python -m pytest tests/test_geo_math_destination.py -v`  
Expected: FAIL `ImportError` / `destination_point` missing

- [ ] **Step 3: Implement destination_point + config + schemas**

Add to `geo_math.py`:

```python
def destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng:
    """Move from origin along initial bearing by distance_km (spherical Earth)."""
    if distance_km <= 0:
        return LatLng(lat=origin.lat, lng=origin.lng)
    lat1 = math.radians(origin.lat)
    lng1 = math.radians(origin.lng)
    brng = math.radians(bearing_degrees)
    angular = (distance_km * 1000.0) / EARTH_RADIUS_M
    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular)
        + math.cos(lat1) * math.sin(angular) * math.cos(brng)
    )
    lng2 = lng1 + math.atan2(
        math.sin(brng) * math.sin(angular) * math.cos(lat1),
        math.cos(angular) - math.sin(lat1) * math.sin(lat2),
    )
    return LatLng(lat=math.degrees(lat2), lng=((math.degrees(lng2) + 540) % 360) - 180)
```

Append to `Settings` in `config.py`:

```python
    nowcast_model_name: str = "baseline"
    nowcast_model_version: str = "0.1"
    nowcast_horizons_minutes: list[int] = [5, 10, 15, 30, 60]
    nowcast_intensity_max: float = 255.0
    nowcast_min_frames_for_full_confidence: int = 3
```

Create `backend/app/schemas/nowcasting.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import LatLng
from app.schemas.rain_cell import CellBoundsOut

NowcastStatus = Literal["ok", "partial", "unavailable"]


class NowcastPredictRequest(BaseModel):
    geometry: list[LatLng] = Field(..., min_length=2)
    buffer_km: float | None = Field(default=None, ge=1, le=300)


class NowcastModelInfo(BaseModel):
    name: str
    version: str


class PredictedCellMotion(BaseModel):
    speed_kmh: float | None = None
    bearing_degrees: float | None = None


class PredictedRainCell(BaseModel):
    cell_id: str
    forecast_minutes: int
    kind: Literal["predicted"] = "predicted"
    centroid: LatLng
    bounds: CellBoundsOut | None = None
    rain_probability: float | None = Field(default=None, ge=0, le=1)
    rain_intensity: float | None = None
    confidence: float = Field(..., ge=0, le=1)
    motion: PredictedCellMotion | None = None
    source: str = "rain_cell_track+baseline"


class NowcastPredictionResponse(BaseModel):
    generated_at: datetime
    status: NowcastStatus
    model: NowcastModelInfo
    frames_used: int
    radar_age_seconds: int | None = None
    horizons: list[int]
    predictions: list[PredictedRainCell]
    message: str | None = None
```

- [ ] **Step 4: Re-run destination tests — expect pass**

Run: `cd backend; python -m pytest tests/test_geo_math_destination.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/geo_math.py backend/app/config.py backend/app/schemas/nowcasting.py backend/tests/test_geo_math_destination.py
# commit via git.exe -F if wrapper breaks
```

Message: `feat(nowcast): add geo destination helper and nowcasting schemas`

---

### Task 2: BaselineExtrapolationModel (TDD core)

**Files:**
- Create: `backend/app/engine/nowcasting_models.py`
- Create: `backend/tests/test_nowcasting_baseline.py`

**Interfaces:**
- Consumes: `TrackedRainCellOut`, `destination_point`, settings horizons / intensity max
- Produces:
  - `class NowcastingModel(Protocol): def predict(self, cells, *, frames_used: int, radar_age_seconds: int | None, horizons: list[int]) -> list[PredictedRainCell]`
  - `class BaselineExtrapolationModel: ...` with `name`/`version` properties
  - Helpers used by tests: intensity trend, confidence decay (can be module-private)

**Algorithm locked by tests:**
- Eligible states: `TRACKING`, `NEW` only
- Distance km = `speed_kmh * (forecast_minutes / 60)`
- Missing speed or bearing → hold centroid/bounds; confidence ≤ 0.35 for that cell-horizon
- Intensity: linear slope from history means if ≥2 samples; else current mean; clamp `[0, nowcast_intensity_max]`
- `rain_probability = clamp(intensity / nowcast_intensity_max, 0, 1)` (None if intensity None)
- Confidence base = `motion.confidence` or `0.4`; multiply by horizon factor `max(0.25, 1 - forecast_minutes/90)`; ×0.7 if `frames_used < nowcast_min_frames_for_full_confidence`; ×0.75 if `len(history) < 2`; ×0.5 if missing motion vector; if `radar_age_seconds` and `> settings.radar_stale_after_seconds` ×0.6

- [ ] **Step 1: Write failing baseline tests**

Create `backend/tests/test_nowcasting_baseline.py` with fixtures building `TrackedRainCellOut` + `CellMotionOut` + history. Cover at minimum:

```python
def test_horizons_emit_five_predictions_per_cell():
    ...
    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=[5, 10, 15, 30, 60])
    assert sorted({p.forecast_minutes for p in preds}) == [5, 10, 15, 30, 60]
    assert all(p.kind == "predicted" for p in preds)
    assert all(p.cell_id == "c1" for p in preds)


def test_projects_centroid_with_speed_and_bearing():
    # speed 60 km/h east → +5 min ≈ 5 km east
    ...


def test_missing_velocity_holds_position_low_confidence():
    ...


def test_missing_direction_holds_position_low_confidence():
    ...


def test_intensity_extrapolates_from_history():
    ...


def test_intensity_fallback_without_history():
    ...


def test_confidence_decreases_with_horizon():
    confs = [p.confidence for p in preds if p.cell_id == "c1"]
    assert confs == sorted(confs, reverse=True)


def test_stale_radar_reduces_confidence():
    ...


def test_short_history_reduces_confidence():
    ...


def test_lost_cells_omitted():
    ...


def test_no_cells_returns_empty():
    assert model.predict([], frames_used=3, radar_age_seconds=60, horizons=[5, 10, 15, 30, 60]) == []
```

Use `haversine_distance_m` assertions (±500 m tolerance for 5 km projection).

- [ ] **Step 2: Run tests — expect fail**

Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py -v`  
Expected: FAIL import / missing module

- [ ] **Step 3: Implement `nowcasting_models.py`**

Implement protocol + `BaselineExtrapolationModel` exactly matching the algorithm above. Translate bounds by the same lat/lng delta as centroid when bounds exist. Set `source="rain_cell_track+baseline"`, `motion` from input speed/bearing used.

- [ ] **Step 4: Run tests — expect pass**

Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py -v`  
Expected: all PASS

- [ ] **Step 5: Commit**

Message: `feat(nowcast): add baseline extrapolation model`

---

### Task 3: NowcastingEngine

**Files:**
- Create: `backend/app/engine/nowcasting_engine.py`
- Create: `backend/tests/test_nowcasting_engine.py`

**Interfaces:**
- Consumes: `RainCellTrackResponse`, `BaselineExtrapolationModel` (or injected `NowcastingModel`)
- Produces: `def run_nowcast(track: RainCellTrackResponse, *, model: NowcastingModel | None = None, generated_at: datetime | None = None) -> NowcastPredictionResponse`

Status rules:
- `track.status == "unavailable"` → response `unavailable`, predictions `[]`, keep track message (or Vietnamese default)
- `track.status == "partial"` → response `partial` (even if predictions exist)
- Else if any predicted cell has confidence < 0.35 due to missing motion → `partial` with message about incomplete motion
- Else `ok`
- Always set `model` from active model name/version, `horizons` from settings, `frames_used` from track
- `radar_age_seconds`: leave `None` in Stage 5 unless easily derived; engine accepts optional override kwarg default `None`

- [ ] **Step 1: Write engine tests**

```python
def test_engine_unavailable_passthrough():
    ...

def test_engine_empty_cells_ok_with_message():
    # track ok, cells=[] → status ok, predictions=[], message tiếng Việt
    ...

def test_engine_runs_baseline_and_sets_model_info():
    ...

def test_engine_partial_when_track_partial():
    ...
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement engine**

```python
def run_nowcast(...):
    model = model or BaselineExtrapolationModel()
    horizons = list(settings.nowcast_horizons_minutes)
    info = NowcastModelInfo(name=model.name, version=model.version)
    if track.status == "unavailable":
        return NowcastPredictionResponse(...)
    preds = model.predict(track.cells, frames_used=track.frames_used, radar_age_seconds=radar_age_seconds, horizons=horizons)
    # status resolution...
```

Expose `name`/`version` properties on baseline model reading from settings.

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

Message: `feat(nowcast): add nowcasting engine orchestrator`

---

### Task 4: Service + API + main registration

**Files:**
- Create: `backend/app/services/nowcasting_service.py`
- Create: `backend/app/api/nowcasting.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_nowcasting_api.py`

**Interfaces:**
- `NowcastingService.predict_for_route(geometry, buffer_km=None) -> NowcastPredictionResponse`
- Internally: `track = await get_rain_cell_service().track_for_route(...)` then `return run_nowcast(track)`
- `get_nowcasting_service()` singleton like rain cells
- Router: `@router.post("/api/nowcasting/predict", response_model=NowcastPredictionResponse)`

- [ ] **Step 1: Write API test with mocked nowcasting service**

Mirror `test_rain_cells_api.py`: patch `app.services.nowcasting_service._nowcasting_service` with `AsyncMock` returning a filled `NowcastPredictionResponse`, POST geometry, assert 200 + `model.name == "baseline"` + horizons + `predictions[0].kind == "predicted"`.

Also add one unit-style test that `NowcastingService.predict_for_route` calls rain-cell track then engine (mock `get_rain_cell_service`).

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement service + API; register in `main.py`**

In `main.py`, inside the successful boot block, after rain-cells try/except, add similar:

```python
    try:
        from app.api.nowcasting import router as nowcasting_router
        app.include_router(nowcasting_router)
    except Exception:
        logging.getLogger(__name__).exception("Nowcasting router failed to load")
```

- [ ] **Step 4: Run API + engine + baseline suite**

Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py -v`  
Expected: all PASS

- [ ] **Step 5: Commit**

Message: `feat(nowcast): expose POST /api/nowcasting/predict`

---

### Task 5: Frontend types + `useNowcasting`

**Files:**
- Create: `frontend/app/types/nowcasting.ts`
- Create: `frontend/app/composables/useNowcasting.ts`
- Create: `frontend/app/utils/nowcast.ts`

**Interfaces:**
- Mirror backend types (`NowcastPredictionResponse`, `PredictedRainCell`, horizons union)
- `useNowcasting()` returns: `enabled`, `selectedHorizon` (`0 | 5 | 10 | 15 | 30 | 60` where `0` = NOW), `loading`, `errorMessage`, `response`, `predictionsForHorizon` computed, `setEnabled`, `setHorizon`, `fetchNowcast(geometry)`, refresh every 300s when enabled
- `predictionsForHorizon`: filter `response.predictions` by `forecast_minutes === selectedHorizon` when horizon > 0; empty when NOW
- `utils/nowcast.ts`: `nowcastGeoJson(cells: PredictedRainCell[])`, `intensityLabel(intensity: number | null): string`, reuse `bearingToCompass` from `rainCell.ts`

- [ ] **Step 1: Add types + composable + utils** (no separate Jest in repo — verify by TypeScript usage and manual later)

`useNowcasting.ts` pattern copy from `useRainCells.ts` but endpoint `/api/nowcasting/predict` and keep `selectedHorizon` in `useState("nowcast-horizon", () => 0)`.

Intensity labels (Vietnamese): null → `Không rõ`; `<40` nhẹ; `<90` vừa; else mạnh (thresholds aligned to RainViewer-ish scale).

- [ ] **Step 2: Commit**

Message: `feat(nowcast): add frontend types and useNowcasting composable`

---

### Task 6: RadarControls — toggle + timeline

**Files:**
- Modify: `frontend/app/components/RadarControls.vue`

**Interfaces:**
- New props: `nowcastingEnabled`, `nowcastingLoading`, `nowcastingError`, `nowcastingModelLabel`, `selectedHorizon`, `nowcastPredictionCount`, `routeReady` (already exists)
- Emits: `update:nowcastingEnabled`, `update:selectedHorizon`
- When `nowcastingEnabled && routeReady`, show timeline buttons: `NOW`, `+5m`, `+10m`, `+15m`, `+30m`, `+60m`
- Show small note: `Dự báo baseline — không phải radar quan sát` + model label

- [ ] **Step 1: Extend props/emits/template** following existing rain-cells toggle markup (checkbox + status lines). Horizon buttons: highlight selected with existing accent classes.

- [ ] **Step 2: Commit**

Message: `feat(nowcast): add nowcasting toggle and horizon timeline UI`

---

### Task 7: RouteMap predicted layers + inspection panel

**Files:**
- Modify: `frontend/app/components/RouteMap.vue`
- Optionally small helper already in `utils/nowcast.ts`

**Interfaces:**
- New props: `nowcastingEnabled?: boolean`, `selectedHorizon?: number`, `predictedCells?: PredictedRainCell[]`, `nowcastModel?: { name: string; version: string } | null`
- Layers (distinct IDs): `nowcast-bbox`, `nowcast-points` — dashed line / teal fill opacity ~0.15, circle color `#2dd4bf`, text field `+{forecast_minutes}m` if MapLibre symbol feasible; otherwise popup only
- Show layers only when `nowcastingEnabled && selectedHorizon > 0 && predictedCells.length`
- Click → popup Vietnamese fields: Nowcasting, forecast, probability %, intensity label, confidence %, movement, model Baseline v0.1, disclaimer predicted
- Do not reuse observed rain-cell layer IDs or colors (observed uses yellow/red)

- [ ] **Step 1: Implement GeoJSON update watchers mirroring rain-cell pattern in `RouteMap.vue`**

- [ ] **Step 2: Manual sanity (dev server) optional; ensure no TS errors in component

- [ ] **Step 3: Commit**

Message: `feat(nowcast): render predicted rain cells on map`

---

### Task 8: Wire `index.vue` + README

**Files:**
- Modify: `frontend/app/pages/index.vue`
- Modify: `README.md`

**Wiring:**
- Import `useNowcasting`
- On analyze success / geometry available: if nowcasting enabled, `fetchNowcast(geometry)` (same geometry as rain cells)
- Pass props to `RadarControls` and `RouteMap`
- `onRefreshLayers` also refreshes nowcast when enabled
- README: Stage 5 section describing baseline architecture diagram (short), how to call API, how to toggle UI; mark roadmap `[x] Stage 5` only after feature works — during this task set to `[x]` and note baseline limitations

- [ ] **Step 1: Wire page**

- [ ] **Step 2: Update README Stage 5**

Include:
- Architecture one-liner matching spec
- `POST /api/nowcasting/predict`
- Baseline ≠ trained ML
- How to test locally (backend pytest + UI toggle)

- [ ] **Step 3: Run full backend nowcast-related tests**

Run: `cd backend; python -m pytest tests/test_geo_math_destination.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v`  
Expected: all PASS (Stage 3/4 unbroken)

- [ ] **Step 4: Commit**

Message: `feat(nowcast): wire Stage 5 UI and document baseline nowcasting`

---

## Spec coverage checklist (self-review)

| Spec requirement | Task |
|---|---|
| Modular engine + model interface | 2, 3 |
| Baseline model baseline/0.1 | 2 |
| Reuse rain-cell tracking | 4 |
| Horizons 5/10/15/30/60 | 1–2 |
| Geometry + intensity + probability + confidence | 2 |
| `kind=predicted` + provenance | 2, 7 |
| API endpoint | 4 |
| Toggle + timeline UI | 6, 8 |
| Distinct map layers + inspect panel | 7 |
| Missing/stale handling | 2, 3 |
| Tests listed in spec | 1–4 |
| Docs / ML insertion point | Spec already + README Task 8 |
| No Stage 1–4 rewrite | All tasks additive |

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-25-stage5-ai-nowcasting.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints  

Which approach?

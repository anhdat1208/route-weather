# Final whole-branch review package
MERGE_BASE: a5a9a91db763730f22e8cc1c9a4e9f143e38aba5
HEAD: 795d72da88c3557bc08995c0d23f90dc7792b05c

## Commits


## Stat
 README.md                                          |  47 +-
 backend/app/api/nowcasting.py                      |  16 -
 backend/app/config.py                              |   6 -
 backend/app/engine/geo_math.py                     |  19 -
 backend/app/engine/nowcasting_engine.py            |  79 ---
 backend/app/engine/nowcasting_models.py            | 207 --------
 backend/app/main.py                                |   8 -
 backend/app/schemas/nowcasting.py                  |  50 --
 backend/app/services/nowcasting_service.py         |  28 --
 backend/tests/test_geo_math_destination.py         |  21 -
 backend/tests/test_nowcasting_api.py               | 102 ----
 backend/tests/test_nowcasting_baseline.py          | 214 ---------
 backend/tests/test_nowcasting_engine.py            | 157 ------
 .../plans/2026-08-25-stage5-ai-nowcasting.md       | 535 ---------------------
 .../2026-08-25-stage5-ai-nowcasting-design.md      | 329 -------------
 frontend/app/components/RadarControls.vue          |  66 ---
 frontend/app/components/RouteMap.vue               | 173 +------
 frontend/app/composables/useNowcasting.ts          | 105 ----
 frontend/app/pages/index.vue                       |  43 --
 frontend/app/types/nowcasting.ts                   |  45 --
 frontend/app/utils/nowcast.ts                      | 125 -----
 21 files changed, 8 insertions(+), 2367 deletions(-)

## Diff
diff --git a/README.md b/README.md
index 8d63b05..81bc99e 100644
--- a/README.md
+++ b/README.md
@@ -63,17 +63,18 @@ RainViewer tiles (corridor)
 User ΓåÆ RouteForm
          Γåô
   useRouteWeather ΓöÇΓöÇΓåÆ POST /api/route-weather ΓåÆ RouteWeatherEngine
   useRadar       ΓöÇΓöÇΓåÆ GET /api/radar/current  ΓåÆ RadarService ΓåÆ RainViewer
   useRainCells   ΓöÇΓöÇΓåÆ POST /api/rain-cells/track ΓåÆ RainCellService
+  useNowcasting  ΓöÇΓöÇΓåÆ POST /api/nowcasting/predict ΓåÆ NowcastingService
          Γåô
-  RouteMap (Base ΓåÆ Radar ΓåÆ Rain Cells ΓåÆ Route ΓåÆ Weather points)
+  RouteMap (Base ΓåÆ Radar ΓåÆ Rain Cells ΓåÆ Predicted nowcast ΓåÆ Route ΓåÆ Weather points)
          +
   RadarControls + JourneySummary + WeatherTimeline
 ```
 
-Map layers: Base ΓåÆ Radar (Stage 2) ΓåÆ Rain Cells (Stage 3) ΓåÆ Route ΓåÆ Weather points.
+Map layers: Base ΓåÆ Radar (Stage 2) ΓåÆ Rain Cells (Stage 3) ΓåÆ Predicted nowcast (Stage 5) ΓåÆ Route ΓåÆ Weather points.
 
 ## Y├¬u cß║ºu
 
 - Docker & Docker Compose (t├╣y chß╗ìn)
 - Node.js 22+ (frontend)
@@ -187,10 +188,11 @@ Kh├┤ng commit credentials thß║¡t.
 | GET | `/api/geocode` | Autocomplete ─æß╗ïa chß╗ë |
 | POST | `/api/route-weather` | Route + weather (single compute) |
 | GET | `/api/radar/current` | Metadata radar hiß╗çn tß║íi (tile URL, timestamp) |
 | GET | `/api/satellite/latest` | Metadata ß║únh vß╗ç tinh hiß╗çn tß║íi (tile URL, timestamp) |
 | POST | `/api/rain-cells/track` | Detect + track v├╣ng m╞░a trong h├ánh lang lß╗Ö tr├¼nh |
+| POST | `/api/nowcasting/predict` | Dß╗▒ b├ío vß╗ï tr├¡ v├╣ng m╞░a 5ΓÇô60 ph├║t (baseline extrapolation) |
 | POST | `/api/weather-fusion/state` | Unified multi-source weather state theo route segment |
 | POST | `/api/route-weather/compare` | So s├ính giß╗¥ xuß║Ñt ph├ít (backend; UI Stage 1 kh├┤ng d├╣ng) |
 
 ## Known limitations
 
@@ -203,25 +205,27 @@ Kh├┤ng commit credentials thß║¡t.
 - ETA ch╞░a t├¡nh traffic
 - Geocoding ─æ╞░ß╗¥ng nhß╗Å ß╗ƒ VN c├│ thß╗â lß╗çch
 - Dß╗▒ b├ío mang t├¡nh x├íc suß║Ñt
 - Satellite Stage 4 fuse theo metadata thß╗¥i gian/chß║Ñt l╞░ß╗úng/provenance; ch╞░a decode pixel ß║únh vß╗ç tinh (feature hiß╗çn tß║íi lß║Ñy tß╗½ forecast + rain-cell + timestamp)
 - Conflict radar-satellite d├╣ng deterministic threshold, kh├┤ng tß╗▒ quyß║┐t ─æß╗ïnh nguß╗ôn n├áo ΓÇ£─æ├║ngΓÇ¥ h╞ín
+- Nowcasting Stage 5 l├á baseline extrapolation (`baseline` / `0.1`), kh├┤ng phß║úi ML ─æ├ú train; confidence giß║úm theo horizon; thiß║┐u vß║¡n tß╗æc th├¼ giß╗» vß╗ï tr├¡; kh├┤ng thay thß║┐ radar quan s├ít
 
 ## Roadmap
 
 - [x] Stage 1 ΓÇö Route Weather MVP
 - [x] Stage 2 ΓÇö Live Radar
 - [x] Stage 3 ΓÇö Rain-cell Detection & Tracking
 - [x] Stage 4 ΓÇö Satellite + Data Fusion
-- [ ] Stage 5 ΓÇö AI Nowcasting
+- [x] Stage 5 ΓÇö AI Nowcasting
 - [ ] Stage 6 ΓÇö Traffic Prediction
 - [ ] Stage 7 ΓÇö Route Weather Intelligence
 
 ## T├ái liß╗çu
 
 - [Design Spec Stage 1](docs/superpowers/specs/2026-08-21-route-weather-stage1-design.md)
 - [Design Spec Stage 3](docs/superpowers/specs/2026-08-24-stage3-rain-cell-tracking-design.md)
+- [Design Spec Stage 5](docs/superpowers/specs/2026-08-25-stage5-ai-nowcasting-design.md)
 - [Implementation Plan](docs/superpowers/plans/2026-08-21-route-weather-stage1.md)
 
 ## Stage 4 ΓÇö Satellite + Multi-source Data Fusion
 
 Stage 4 t├¡ch hß╗úp dß╗» liß╗çu vß╗ç tinh v├á th├¬m lß╗¢p fusion deterministic ─æß╗â tß║ío trß║íng th├íi thß╗¥i tiß║┐t hß╗úp nhß║Ñt theo route segment, c├│ temporal alignment, freshness v├á provenance.
@@ -238,9 +242,42 @@ Implemented:
 - per-segment confidence (0ΓÇô1) tß╗½ freshness/quality/conflict
 - deterministic nowcast features tr├¬n tß╗½ng segment (`precip_evidence`, age, overlap, ΓÇª) cho Stage 5
 - fusion debug panel (dev / `NUXT_PUBLIC_ENABLE_FUSION_DEBUG=true`)
 
 Not implemented:
-- AI/ML
-- future prediction
+- trained ML / deep learning (Stage 5 chß╗ë baseline extrapolation)
 - traffic prediction
 - final route risk engine
+
+## Stage 5 ΓÇö AI Nowcasting (baseline)
+
+Stage 5 trß║ú lß╗¥i: v├╣ng m╞░a ─æang theo d├╡i sß║╜ **c├│ thß╗â** ß╗ƒ ─æ├óu trong 5ΓÇô60 ph├║t tß╗¢i. Pipeline: tracking Stage 3 ΓåÆ `NowcastingEngine` ΓåÆ `BaselineExtrapolationModel` (`name=baseline`, `version=0.1`) ΓåÆ API + lß╗¢p predicted tr├¬n map.
+
+─É├óy **kh├┤ng phß║úi** m├┤ h├¼nh ML/DL ─æ├ú train ΓÇö chß╗ë extrapolation chuyß╗ân ─æß╗Öng (tß╗æc ─æß╗Ö/h╞░ß╗¢ng quan s├ít). Chß╗ù cß║»m model sau kh├┤ng ─æß╗òi API/UI.
+
+```text
+Route geometry
+  ΓåÆ POST /api/nowcasting/predict
+  ΓåÆ NowcastingService
+  ΓåÆ RainCellService.track_for_route   ΓåÉ Stage 3 reuse
+  ΓåÆ NowcastingEngine
+  ΓåÆ BaselineExtrapolationModel (v0.1)
+  ΓåÆ useNowcasting ΓåÆ RouteMap (predicted layers) + timeline NOW/+5mΓÇª/+60m
+```
+
+**C├│ th├¬m:**
+- `POST /api/nowcasting/predict` vß╗¢i `{ geometry, buffer_km? }`
+- Toggle **Nowcasting (dß╗▒ b├ío m╞░a)** v├á timeline `NOW / +5m / +10m / +15m / +30m / +60m`
+- Lß╗¢p predicted ri├¬ng (teal, dashed) ΓÇö kh├┤ng vß║╜ nh╞░ radar quan s├ít
+
+**Giß╗¢i hß║ín baseline:** tuyß║┐n t├¡nh theo vß║¡n tß╗æc hiß╗çn tß║íi; thiß║┐u vß║¡n tß╗æc th├¼ giß╗» vß╗ï tr├¡ + confidence thß║Ñp; horizon c├áng xa c├áng k├⌐m tin cß║¡y; kh├┤ng storm-cell typing, kh├┤ng route-risk.
+
+### C├ích test local
+
+Backend:
+
+```bash
+cd backend
+python -m pytest tests/test_geo_math_destination.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v
+```
+
+UI: ph├ón t├¡ch lß╗Ö tr├¼nh ΓåÆ bß║¡t **Nowcasting (dß╗▒ b├ío m╞░a)** ΓåÆ chß╗ìn `+5m`ΓÇª`+60m` ─æß╗â xem v├╣ng m╞░a dß╗▒ b├ío. `NOW` chß╗ë hiß╗çn lß╗¢p quan s├ít (radar / rain cells). N├║t **L├ám mß╗¢i** c┼⌐ng refresh nowcast khi toggle ─æang bß║¡t.
diff --git a/backend/app/api/nowcasting.py b/backend/app/api/nowcasting.py
new file mode 100644
index 0000000..511ce8f
--- /dev/null
+++ b/backend/app/api/nowcasting.py
@@ -0,0 +1,16 @@
+from __future__ import annotations
+
+from fastapi import APIRouter
+
+from app.schemas.nowcasting import NowcastPredictRequest, NowcastPredictionResponse
+from app.services.nowcasting_service import get_nowcasting_service
+
+router = APIRouter(tags=["nowcasting"])
+
+
+@router.post("/api/nowcasting/predict", response_model=NowcastPredictionResponse)
+async def nowcasting_predict(body: NowcastPredictRequest) -> NowcastPredictionResponse:
+    """Predict rain-cell motion along a route corridor (baseline extrapolation)."""
+    return await get_nowcasting_service().predict_for_route(
+        body.geometry, buffer_km=body.buffer_km
+    )
diff --git a/backend/app/config.py b/backend/app/config.py
index 3c587bc..9d575a9 100644
--- a/backend/app/config.py
+++ b/backend/app/config.py
@@ -83,10 +83,16 @@ class Settings(BaseSettings):
     risk_threshold_low: int = 20
     risk_threshold_moderate: int = 40
     risk_threshold_high: int = 60
     risk_threshold_very_high: int = 80
 
+    nowcast_model_name: str = "baseline"
+    nowcast_model_version: str = "0.1"
+    nowcast_horizons_minutes: list[int] = [5, 10, 15, 30, 60]
+    nowcast_intensity_max: float = 255.0
+    nowcast_min_frames_for_full_confidence: int = 3
+
     # Server
     backend_host: str = "0.0.0.0"
     backend_port: int = 8000
     cors_origins: str = "http://localhost:3000,https://route-weather-tracking.vercel.app"
 
diff --git a/backend/app/engine/geo_math.py b/backend/app/engine/geo_math.py
index ca631a4..6797381 100644
--- a/backend/app/engine/geo_math.py
+++ b/backend/app/engine/geo_math.py
@@ -6,10 +6,29 @@ from app.schemas.common import LatLng
 
 
 EARTH_RADIUS_M = 6371000.0
 
 
+def destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng:
+    """Move from origin along initial bearing by distance_km (spherical Earth)."""
+    if distance_km <= 0:
+        return LatLng(lat=origin.lat, lng=origin.lng)
+    lat1 = math.radians(origin.lat)
+    lng1 = math.radians(origin.lng)
+    brng = math.radians(bearing_degrees)
+    angular = (distance_km * 1000.0) / EARTH_RADIUS_M
+    lat2 = math.asin(
+        math.sin(lat1) * math.cos(angular)
+        + math.cos(lat1) * math.sin(angular) * math.cos(brng)
+    )
+    lng2 = lng1 + math.atan2(
+        math.sin(brng) * math.sin(angular) * math.cos(lat1),
+        math.cos(angular) - math.sin(lat1) * math.sin(lat2),
+    )
+    return LatLng(lat=math.degrees(lat2), lng=((math.degrees(lng2) + 540) % 360) - 180)
+
+
 def haversine_distance_m(a: LatLng, b: LatLng) -> float:
     """Distance in meters between two WGS84 points."""
 
     lat1 = math.radians(a.lat)
     lat2 = math.radians(b.lat)
diff --git a/backend/app/engine/nowcasting_engine.py b/backend/app/engine/nowcasting_engine.py
new file mode 100644
index 0000000..d7b64dd
--- /dev/null
+++ b/backend/app/engine/nowcasting_engine.py
@@ -0,0 +1,79 @@
+from __future__ import annotations
+
+from datetime import datetime, timezone
+
+from app.config import settings
+from app.engine.nowcasting_models import BaselineExtrapolationModel, NowcastingModel
+from app.schemas.nowcasting import NowcastModelInfo, NowcastPredictionResponse, PredictedRainCell
+from app.schemas.rain_cell import RainCellTrackResponse
+
+_MSG_UNAVAILABLE = "Dß╗» liß╗çu theo d├╡i ├┤ m╞░a tß║ím thß╗¥i kh├┤ng khß║ú dß╗Ñng."
+_MSG_EMPTY = "Kh├┤ng c├│ ├┤ m╞░a ─æang theo d├╡i ─æß╗â dß╗▒ b├ío."
+_MSG_INCOMPLETE_MOTION = "Mß╗Öt sß╗æ ├┤ m╞░a thiß║┐u vector chuyß╗ân ─æß╗Öng n├¬n dß╗▒ b├ío ch╞░a ─æß║ºy ─æß╗º."
+
+
+def _missing_motion(pred: PredictedRainCell) -> bool:
+    motion = pred.motion
+    if motion is None:
+        return True
+    return motion.speed_kmh is None or motion.bearing_degrees is None
+
+
+def _has_incomplete_motion(preds: list[PredictedRainCell]) -> bool:
+    return any(pred.confidence < 0.35 and _missing_motion(pred) for pred in preds)
+
+
+def run_nowcast(
+    track: RainCellTrackResponse,
+    *,
+    model: NowcastingModel | None = None,
+    generated_at: datetime | None = None,
+    radar_age_seconds: int | None = None,
+) -> NowcastPredictionResponse:
+    active = model or BaselineExtrapolationModel()
+    horizons = list(settings.nowcast_horizons_minutes)
+    info = NowcastModelInfo(name=active.name, version=active.version)
+    at = generated_at or datetime.now(timezone.utc)
+
+    if track.status == "unavailable":
+        return NowcastPredictionResponse(
+            generated_at=at,
+            status="unavailable",
+            model=info,
+            frames_used=track.frames_used,
+            radar_age_seconds=radar_age_seconds,
+            horizons=horizons,
+            predictions=[],
+            message=track.message or _MSG_UNAVAILABLE,
+        )
+
+    preds = active.predict(
+        track.cells,
+        frames_used=track.frames_used,
+        radar_age_seconds=radar_age_seconds,
+        horizons=horizons,
+    )
+
+    if track.status == "partial":
+        status = "partial"
+        message = track.message
+    elif _has_incomplete_motion(preds):
+        status = "partial"
+        message = _MSG_INCOMPLETE_MOTION
+    elif not preds:
+        status = "ok"
+        message = _MSG_EMPTY
+    else:
+        status = "ok"
+        message = None
+
+    return NowcastPredictionResponse(
+        generated_at=at,
+        status=status,
+        model=info,
+        frames_used=track.frames_used,
+        radar_age_seconds=radar_age_seconds,
+        horizons=horizons,
+        predictions=preds,
+        message=message,
+    )
diff --git a/backend/app/engine/nowcasting_models.py b/backend/app/engine/nowcasting_models.py
new file mode 100644
index 0000000..ca815f8
--- /dev/null
+++ b/backend/app/engine/nowcasting_models.py
@@ -0,0 +1,207 @@
+from __future__ import annotations
+
+from datetime import datetime
+from typing import Protocol, Sequence
+
+from app.config import settings
+from app.engine.geo_math import destination_point
+from app.schemas.common import LatLng
+from app.schemas.nowcasting import PredictedCellMotion, PredictedRainCell
+from app.schemas.rain_cell import CellBoundsOut, TrackedRainCellOut
+
+_ELIGIBLE_STATES = frozenset({"TRACKING", "NEW"})
+
+
+class NowcastingModel(Protocol):
+    def predict(
+        self,
+        cells: Sequence[TrackedRainCellOut],
+        *,
+        frames_used: int,
+        radar_age_seconds: int | None,
+        horizons: list[int],
+    ) -> list[PredictedRainCell]: ...
+
+
+def _parse_timestamp(value: str) -> datetime | None:
+    try:
+        return datetime.fromisoformat(value.replace("Z", "+00:00"))
+    except ValueError:
+        return None
+
+
+def _intensity_samples(cell: TrackedRainCellOut) -> list[tuple[float, float]]:
+    dated: list[tuple[datetime, float]] = []
+    for item in (*cell.history, cell.current):
+        if item.intensity is None or item.intensity.mean is None:
+            continue
+        parsed = _parse_timestamp(item.timestamp)
+        if parsed is None:
+            continue
+        dated.append((parsed, item.intensity.mean))
+    if not dated:
+        return []
+    dated.sort(key=lambda pair: pair[0])
+    origin = dated[0][0]
+    return [((ts - origin).total_seconds() / 60.0, mean) for ts, mean in dated]
+
+
+def _linear_slope(samples: list[tuple[float, float]]) -> float:
+    n = len(samples)
+    xs = [x for x, _ in samples]
+    ys = [y for _, y in samples]
+    mean_x = sum(xs) / n
+    mean_y = sum(ys) / n
+    denom = sum((x - mean_x) ** 2 for x in xs)
+    if denom == 0:
+        return 0.0
+    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / denom
+
+
+def _extrapolate_intensity(cell: TrackedRainCellOut, forecast_minutes: int) -> float | None:
+    current_mean = cell.current.intensity.mean if cell.current.intensity is not None else None
+    samples = _intensity_samples(cell)
+    if len(samples) >= 2:
+        base = current_mean if current_mean is not None else samples[-1][1]
+        predicted = base + _linear_slope(samples) * forecast_minutes
+    else:
+        predicted = current_mean
+    if predicted is None:
+        return None
+    return max(0.0, min(float(settings.nowcast_intensity_max), predicted))
+
+
+def _confidence(
+    cell: TrackedRainCellOut,
+    *,
+    forecast_minutes: int,
+    frames_used: int,
+    radar_age_seconds: int | None,
+    missing_motion_vector: bool,
+) -> float:
+    motion = cell.motion
+    base = 0.4
+    if motion is not None and motion.confidence is not None:
+        base = motion.confidence
+    value = base * max(0.25, 1 - forecast_minutes / 90)
+    if frames_used < settings.nowcast_min_frames_for_full_confidence:
+        value *= 0.7
+    if len(cell.history) < 2:
+        value *= 0.75
+    if missing_motion_vector:
+        value *= 0.5
+    if radar_age_seconds and radar_age_seconds > settings.radar_stale_after_seconds:
+        value *= 0.6
+    if missing_motion_vector:
+        value = min(value, 0.35)
+    return max(0.0, min(1.0, value))
+
+
+def _copy_latlng(point: LatLng) -> LatLng:
+    return LatLng(lat=point.lat, lng=point.lng)
+
+
+def _copy_bounds(bounds: CellBoundsOut | None) -> CellBoundsOut | None:
+    if bounds is None:
+        return None
+    return CellBoundsOut(north=bounds.north, south=bounds.south, east=bounds.east, west=bounds.west)
+
+
+def _translate_bounds(bounds: CellBoundsOut, dlat: float, dlng: float) -> CellBoundsOut:
+    return CellBoundsOut(
+        north=bounds.north + dlat,
+        south=bounds.south + dlat,
+        east=bounds.east + dlng,
+        west=bounds.west + dlng,
+    )
+
+
+class BaselineExtrapolationModel:
+    @property
+    def name(self) -> str:
+        return settings.nowcast_model_name
+
+    @property
+    def version(self) -> str:
+        return settings.nowcast_model_version
+
+    def predict(
+        self,
+        cells: Sequence[TrackedRainCellOut],
+        *,
+        frames_used: int,
+        radar_age_seconds: int | None,
+        horizons: list[int],
+    ) -> list[PredictedRainCell]:
+        predictions: list[PredictedRainCell] = []
+        for cell in cells:
+            if cell.state not in _ELIGIBLE_STATES:
+                continue
+            predictions.extend(
+                self._predict_cell(
+                    cell,
+                    frames_used=frames_used,
+                    radar_age_seconds=radar_age_seconds,
+                    horizons=horizons,
+                )
+            )
+        return predictions
+
+    def _predict_cell(
+        self,
+        cell: TrackedRainCellOut,
+        *,
+        frames_used: int,
+        radar_age_seconds: int | None,
+        horizons: list[int],
+    ) -> list[PredictedRainCell]:
+        motion = cell.motion
+        speed = motion.speed_kmh if motion is not None else None
+        bearing = motion.bearing_degrees if motion is not None else None
+        missing_motion_vector = speed is None or bearing is None
+        origin = cell.current.centroid
+        origin_bounds = cell.current.bounds
+
+        out: list[PredictedRainCell] = []
+        for forecast_minutes in horizons:
+            if missing_motion_vector:
+                centroid = _copy_latlng(origin)
+                bounds = _copy_bounds(origin_bounds)
+            else:
+                distance_km = float(speed) * (forecast_minutes / 60.0)
+                centroid = destination_point(origin, distance_km, float(bearing))
+                if origin_bounds is None:
+                    bounds = None
+                else:
+                    bounds = _translate_bounds(
+                        origin_bounds,
+                        centroid.lat - origin.lat,
+                        centroid.lng - origin.lng,
+                    )
+
+            intensity = _extrapolate_intensity(cell, forecast_minutes)
+            probability = None
+            if intensity is not None:
+                probability = max(0.0, min(1.0, intensity / settings.nowcast_intensity_max))
+
+            out.append(
+                PredictedRainCell(
+                    cell_id=cell.id,
+                    forecast_minutes=forecast_minutes,
+                    kind="predicted",
+                    centroid=centroid,
+                    bounds=bounds,
+                    rain_probability=probability,
+                    rain_intensity=intensity,
+                    confidence=_confidence(
+                        cell,
+                        forecast_minutes=forecast_minutes,
+                        frames_used=frames_used,
+                        radar_age_seconds=radar_age_seconds,
+                        missing_motion_vector=missing_motion_vector,
+                    ),
+                    motion=PredictedCellMotion(speed_kmh=speed, bearing_degrees=bearing),
+                    source="rain_cell_track+baseline",
+                )
+            )
+        return out
diff --git a/backend/app/main.py b/backend/app/main.py
index 4dcad8f..97dd478 100644
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -40,10 +40,18 @@ try:
         app.include_router(rain_cells_router)
     except Exception:  # noqa: BLE001 - Stage 3 must not take down radar/route APIs
         import logging
 
         logging.getLogger(__name__).exception("Rain-cell router failed to load")
+    try:
+        from app.api.nowcasting import router as nowcasting_router
+
+        app.include_router(nowcasting_router)
+    except Exception:  # noqa: BLE001 - Stage 5 must not take down radar/route APIs
+        import logging
+
+        logging.getLogger(__name__).exception("Nowcasting router failed to load")
 except Exception:  # noqa: BLE001 - surface boot failures on Vercel
     import traceback
 
     _boot_error = traceback.format_exc()
     app.add_middleware(
diff --git a/backend/app/schemas/nowcasting.py b/backend/app/schemas/nowcasting.py
new file mode 100644
index 0000000..29be220
--- /dev/null
+++ b/backend/app/schemas/nowcasting.py
@@ -0,0 +1,50 @@
+from __future__ import annotations
+
+from datetime import datetime
+from typing import Literal
+
+from pydantic import BaseModel, Field
+
+from app.schemas.common import LatLng
+from app.schemas.rain_cell import CellBoundsOut
+
+NowcastStatus = Literal["ok", "partial", "unavailable"]
+
+
+class NowcastPredictRequest(BaseModel):
+    geometry: list[LatLng] = Field(..., min_length=2)
+    buffer_km: float | None = Field(default=None, ge=1, le=300)
+
+
+class NowcastModelInfo(BaseModel):
+    name: str
+    version: str
+
+
+class PredictedCellMotion(BaseModel):
+    speed_kmh: float | None = None
+    bearing_degrees: float | None = None
+
+
+class PredictedRainCell(BaseModel):
+    cell_id: str
+    forecast_minutes: int
+    kind: Literal["predicted"] = "predicted"
+    centroid: LatLng
+    bounds: CellBoundsOut | None = None
+    rain_probability: float | None = Field(default=None, ge=0, le=1)
+    rain_intensity: float | None = None
+    confidence: float = Field(..., ge=0, le=1)
+    motion: PredictedCellMotion | None = None
+    source: str = "rain_cell_track+baseline"
+
+
+class NowcastPredictionResponse(BaseModel):
+    generated_at: datetime
+    status: NowcastStatus
+    model: NowcastModelInfo
+    frames_used: int
+    radar_age_seconds: int | None = None
+    horizons: list[int]
+    predictions: list[PredictedRainCell]
+    message: str | None = None
diff --git a/backend/app/services/nowcasting_service.py b/backend/app/services/nowcasting_service.py
new file mode 100644
index 0000000..08b01f3
--- /dev/null
+++ b/backend/app/services/nowcasting_service.py
@@ -0,0 +1,28 @@
+from __future__ import annotations
+
+from app.engine.nowcasting_engine import run_nowcast
+from app.schemas.common import LatLng
+from app.schemas.nowcasting import NowcastPredictionResponse
+from app.services.rain_cell_service import get_rain_cell_service
+
+
+class NowcastingService:
+    async def predict_for_route(
+        self,
+        geometry: list[LatLng],
+        buffer_km: float | None = None,
+    ) -> NowcastPredictionResponse:
+        track = await get_rain_cell_service().track_for_route(
+            geometry, buffer_km=buffer_km
+        )
+        return run_nowcast(track)
+
+
+_nowcasting_service: NowcastingService | None = None
+
+
+def get_nowcasting_service() -> NowcastingService:
+    global _nowcasting_service
+    if _nowcasting_service is None:
+        _nowcasting_service = NowcastingService()
+    return _nowcasting_service
diff --git a/backend/tests/test_geo_math_destination.py b/backend/tests/test_geo_math_destination.py
new file mode 100644
index 0000000..8075d0e
--- /dev/null
+++ b/backend/tests/test_geo_math_destination.py
@@ -0,0 +1,21 @@
+from __future__ import annotations
+
+from app.engine.geo_math import destination_point, haversine_distance_m
+from app.schemas.common import LatLng
+
+
+def test_destination_point_north_1km():
+    origin = LatLng(lat=10.0, lng=106.0)
+    dest = destination_point(origin, distance_km=1.0, bearing_degrees=0.0)
+    dist_m = haversine_distance_m(origin, dest)
+    assert abs(dist_m - 1000.0) < 15.0
+    assert dest.lat > origin.lat
+    assert abs(dest.lng - origin.lng) < 1e-4
+
+
+def test_destination_point_east_and_zero():
+    origin = LatLng(lat=10.0, lng=106.0)
+    east = destination_point(origin, distance_km=2.0, bearing_degrees=90.0)
+    assert east.lng > origin.lng
+    same = destination_point(origin, distance_km=0.0, bearing_degrees=123.0)
+    assert same.lat == origin.lat and same.lng == origin.lng
diff --git a/backend/tests/test_nowcasting_api.py b/backend/tests/test_nowcasting_api.py
new file mode 100644
index 0000000..cce440e
--- /dev/null
+++ b/backend/tests/test_nowcasting_api.py
@@ -0,0 +1,102 @@
+from __future__ import annotations
+
+from datetime import datetime, timezone
+from unittest.mock import AsyncMock, patch
+
+import pytest
+from httpx import ASGITransport, AsyncClient
+
+from app.main import app
+from app.schemas.common import LatLng
+from app.schemas.nowcasting import (
+    NowcastModelInfo,
+    NowcastPredictionResponse,
+    PredictedCellMotion,
+    PredictedRainCell,
+)
+from app.schemas.rain_cell import CellBoundsOut, RainCellTrackResponse
+from app.services.nowcasting_service import NowcastingService
+
+
+def _filled_prediction() -> NowcastPredictionResponse:
+    return NowcastPredictionResponse(
+        generated_at=datetime(2026, 8, 25, 4, 0, tzinfo=timezone.utc),
+        status="ok",
+        model=NowcastModelInfo(name="baseline", version="0.1"),
+        frames_used=4,
+        horizons=[5, 10, 15, 30, 60],
+        predictions=[
+            PredictedRainCell(
+                cell_id="cell-1",
+                forecast_minutes=5,
+                kind="predicted",
+                centroid=LatLng(lat=10.5, lng=106.5),
+                bounds=CellBoundsOut(
+                    north=10.55,
+                    south=10.45,
+                    east=106.55,
+                    west=106.45,
+                ),
+                rain_probability=0.5,
+                rain_intensity=60.0,
+                confidence=0.8,
+                motion=PredictedCellMotion(speed_kmh=60.0, bearing_degrees=90.0),
+            )
+        ],
+    )
+
+
+@pytest.mark.asyncio
+async def test_nowcasting_predict_endpoint_with_mock_service():
+    from app.services import nowcasting_service as ncs
+
+    mock_response = _filled_prediction()
+    service = AsyncMock()
+    service.predict_for_route = AsyncMock(return_value=mock_response)
+    previous = ncs._nowcasting_service
+    ncs._nowcasting_service = service
+
+    try:
+        transport = ASGITransport(app=app)
+        async with AsyncClient(transport=transport, base_url="http://test") as client:
+            resp = await client.post(
+                "/api/nowcasting/predict",
+                json={
+                    "geometry": [
+                        {"lat": 10.4, "lng": 106.4},
+                        {"lat": 10.6, "lng": 106.6},
+                    ],
+                },
+            )
+    finally:
+        ncs._nowcasting_service = previous
+
+    assert resp.status_code == 200
+    data = resp.json()
+    assert data["model"]["name"] == "baseline"
+    assert data["horizons"] == [5, 10, 15, 30, 60]
+    assert data["predictions"][0]["kind"] == "predicted"
+
+
+@pytest.mark.asyncio
+async def test_predict_for_route_calls_track_then_engine():
+    mock_track = RainCellTrackResponse(status="ok", frames_used=3, cells=[], message=None)
+    rain_svc = AsyncMock()
+    rain_svc.track_for_route = AsyncMock(return_value=mock_track)
+    geometry = [
+        LatLng(lat=10.4, lng=106.4),
+        LatLng(lat=10.6, lng=106.6),
+    ]
+
+    with patch(
+        "app.services.nowcasting_service.get_rain_cell_service",
+        return_value=rain_svc,
+    ):
+        result = await NowcastingService().predict_for_route(geometry, buffer_km=25.0)
+
+    rain_svc.track_for_route.assert_awaited_once_with(geometry, buffer_km=25.0)
+    assert result.status == "ok"
+    assert result.predictions == []
+    assert result.frames_used == 3
+    assert result.model.name == "baseline"
+    assert result.message == "Kh├┤ng c├│ ├┤ m╞░a ─æang theo d├╡i ─æß╗â dß╗▒ b├ío."
diff --git a/backend/tests/test_nowcasting_baseline.py b/backend/tests/test_nowcasting_baseline.py
new file mode 100644
index 0000000..6ea4d27
--- /dev/null
+++ b/backend/tests/test_nowcasting_baseline.py
@@ -0,0 +1,214 @@
+from __future__ import annotations
+
+from datetime import datetime, timedelta, timezone
+
+import pytest
+
+from app.config import settings
+from app.engine.geo_math import haversine_distance_m
+from app.engine.nowcasting_models import BaselineExtrapolationModel
+from app.schemas.common import LatLng
+from app.schemas.rain_cell import (
+    CellBoundsOut,
+    CellIntensityOut,
+    CellMotionOut,
+    RainCellOut,
+    TrackedRainCellOut,
+)
+
+T0 = datetime(2026, 8, 24, 3, 35, tzinfo=timezone.utc)
+ORIGIN = LatLng(lat=10.0, lng=106.0)
+BOUNDS = CellBoundsOut(north=10.05, south=9.95, east=106.05, west=105.95)
+HORIZONS = [5, 10, 15, 30, 60]
+
+
+def _ts(minutes_before: int) -> str:
+    return (T0 - timedelta(minutes=minutes_before)).isoformat()
+
+
+def _cell_out(
+    *,
+    cell_id: str = "c1",
+    minutes_before: int = 0,
+    centroid: LatLng | None = None,
+    mean: float | None = 60.0,
+    bounds: CellBoundsOut | None = BOUNDS,
+) -> RainCellOut:
+    intensity = None if mean is None else CellIntensityOut(min=mean - 10, max=mean + 10, mean=mean)
+    return RainCellOut(
+        id=f"{cell_id}-t{minutes_before}",
+        timestamp=_ts(minutes_before),
+        centroid=centroid or ORIGIN,
+        area_km2=12.0,
+        intensity=intensity,
+        bounds=bounds,
+    )
+
+
+def _tracked(
+    *,
+    cell_id: str = "c1",
+    state: str = "TRACKING",
+    speed_kmh: float | None = 60.0,
+    bearing_degrees: float | None = 90.0,
+    motion_confidence: float | None = 1.0,
+    history_means: list[tuple[int, float]] | None = None,
+    current_mean: float | None = 60.0,
+    include_motion: bool = True,
+) -> TrackedRainCellOut:
+    history_means = history_means if history_means is not None else [(20, 40.0), (10, 50.0)]
+    history = [
+        _cell_out(cell_id=cell_id, minutes_before=mins, mean=mean) for mins, mean in history_means
+    ]
+    motion = None
+    if include_motion:
+        motion = CellMotionOut(
+            speed_kmh=speed_kmh,
+            bearing_degrees=bearing_degrees,
+            from_point=ORIGIN,
+            to_point=ORIGIN,
+            confidence=motion_confidence,
+        )
+    return TrackedRainCellOut(
+        id=cell_id,
+        state=state,  # type: ignore[arg-type]
+        current=_cell_out(cell_id=cell_id, minutes_before=0, mean=current_mean),
+        history=history,
+        motion=motion,
+        missed_frames=0,
+    )
+
+
+def test_horizons_emit_five_predictions_per_cell():
+    model = BaselineExtrapolationModel()
+    cell = _tracked()
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert sorted({p.forecast_minutes for p in preds}) == [5, 10, 15, 30, 60]
+    assert all(p.kind == "predicted" for p in preds)
+    assert all(p.cell_id == "c1" for p in preds)
+    assert all(p.source == "rain_cell_track+baseline" for p in preds)
+    assert model.name == settings.nowcast_model_name
+    assert model.version == settings.nowcast_model_version
+
+
+def test_projects_centroid_with_speed_and_bearing():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(speed_kmh=60.0, bearing_degrees=90.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    plus_5 = next(p for p in preds if p.forecast_minutes == 5)
+    dist_m = haversine_distance_m(ORIGIN, plus_5.centroid)
+    assert abs(dist_m - 5000.0) < 500.0
+    assert plus_5.centroid.lng > ORIGIN.lng
+    assert abs(plus_5.centroid.lat - ORIGIN.lat) < 0.05
+    assert plus_5.bounds is not None
+    assert plus_5.bounds.east > BOUNDS.east
+    assert plus_5.bounds.west > BOUNDS.west
+    assert plus_5.motion is not None
+    assert plus_5.motion.speed_kmh == 60.0
+    assert plus_5.motion.bearing_degrees == 90.0
+
+
+def test_missing_velocity_holds_position_low_confidence():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(speed_kmh=None, bearing_degrees=90.0, motion_confidence=1.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert len(preds) == 5
+    for p in preds:
+        assert p.centroid.lat == ORIGIN.lat
+        assert p.centroid.lng == ORIGIN.lng
+        assert p.bounds is not None
+        assert p.bounds.north == BOUNDS.north
+        assert p.bounds.south == BOUNDS.south
+        assert p.bounds.east == BOUNDS.east
+        assert p.bounds.west == BOUNDS.west
+        assert p.confidence <= 0.35
+
+
+def test_missing_direction_holds_position_low_confidence():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(speed_kmh=60.0, bearing_degrees=None, motion_confidence=1.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert len(preds) == 5
+    for p in preds:
+        assert p.centroid.lat == ORIGIN.lat
+        assert p.centroid.lng == ORIGIN.lng
+        assert p.confidence <= 0.35
+
+
+def test_intensity_extrapolates_from_history():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(history_means=[(20, 40.0), (10, 50.0)], current_mean=60.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    plus_5 = next(p for p in preds if p.forecast_minutes == 5)
+    plus_60 = next(p for p in preds if p.forecast_minutes == 60)
+    assert plus_5.rain_intensity == pytest.approx(65.0)
+    assert plus_60.rain_intensity == pytest.approx(120.0)
+    assert plus_5.rain_probability == pytest.approx(65.0 / settings.nowcast_intensity_max)
+    assert plus_60.rain_probability == pytest.approx(120.0 / settings.nowcast_intensity_max)
+
+
+def test_intensity_fallback_without_history():
+    model = BaselineExtrapolationModel()
+    cell = _tracked(history_means=[], current_mean=80.0)
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    assert len(preds) == 5
+    for p in preds:
+        assert p.rain_intensity == pytest.approx(80.0)
+        assert p.rain_probability == pytest.approx(80.0 / settings.nowcast_intensity_max)
+
+
+def test_confidence_decreases_with_horizon():
+    model = BaselineExtrapolationModel()
+    cell = _tracked()
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    confs = [p.confidence for p in preds if p.cell_id == "c1"]
+    assert confs == sorted(confs, reverse=True)
+    assert len(confs) == 5
+
+
+def test_stale_radar_reduces_confidence():
+    model = BaselineExtrapolationModel()
+    cell = _tracked()
+    fresh = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    stale = model.predict(
+        [cell],
+        frames_used=4,
+        radar_age_seconds=settings.radar_stale_after_seconds + 1,
+        horizons=HORIZONS,
+    )
+    for f, s in zip(fresh, stale, strict=True):
+        assert s.confidence == pytest.approx(f.confidence * 0.6)
+        assert s.confidence < f.confidence
+
+
+def test_short_history_reduces_confidence():
+    model = BaselineExtrapolationModel()
+    long_hist = _tracked(cell_id="c1", history_means=[(20, 40.0), (10, 50.0)])
+    short_hist = _tracked(cell_id="c2", history_means=[])
+    long_preds = model.predict([long_hist], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    short_preds = model.predict([short_hist], frames_used=4, radar_age_seconds=120, horizons=HORIZONS)
+    for long_p, short_p in zip(long_preds, short_preds, strict=True):
+        assert short_p.confidence == pytest.approx(long_p.confidence * 0.75)
+        assert short_p.confidence < long_p.confidence
+
+
+def test_lost_cells_omitted():
+    model = BaselineExtrapolationModel()
+    tracking = _tracked(cell_id="c1", state="TRACKING")
+    lost = _tracked(cell_id="lost", state="LOST")
+    expired = _tracked(cell_id="expired", state="EXPIRED")
+    new = _tracked(cell_id="new", state="NEW")
+    preds = model.predict(
+        [tracking, lost, expired, new],
+        frames_used=4,
+        radar_age_seconds=120,
+        horizons=HORIZONS,
+    )
+    ids = {p.cell_id for p in preds}
+    assert ids == {"c1", "new"}
+    assert len(preds) == 10
+
+
+def test_no_cells_returns_empty():
+    model = BaselineExtrapolationModel()
+    assert model.predict([], frames_used=3, radar_age_seconds=60, horizons=HORIZONS) == []
diff --git a/backend/tests/test_nowcasting_engine.py b/backend/tests/test_nowcasting_engine.py
new file mode 100644
index 0000000..1ab60a0
--- /dev/null
+++ b/backend/tests/test_nowcasting_engine.py
@@ -0,0 +1,157 @@
+from __future__ import annotations
+
+from datetime import datetime, timezone
+
+from app.config import settings
+from app.engine.nowcasting_engine import run_nowcast
+from app.schemas.common import LatLng
+from app.schemas.rain_cell import (
+    CellBoundsOut,
+    CellIntensityOut,
+    CellMotionOut,
+    RainCellOut,
+    RainCellTrackResponse,
+    TrackedRainCellOut,
+)
+
+ORIGIN = LatLng(lat=10.0, lng=106.0)
+BOUNDS = CellBoundsOut(north=10.05, south=9.95, east=106.05, west=105.95)
+GENERATED_AT = datetime(2026, 8, 25, 4, 0, tzinfo=timezone.utc)
+
+
+def _cell(
+    *,
+    cell_id: str = "c1",
+    state: str = "TRACKING",
+    speed_kmh: float | None = 60.0,
+    bearing_degrees: float | None = 90.0,
+    include_motion: bool = True,
+) -> TrackedRainCellOut:
+    motion = None
+    if include_motion:
+        motion = CellMotionOut(
+            speed_kmh=speed_kmh,
+            bearing_degrees=bearing_degrees,
+            from_point=ORIGIN,
+            to_point=ORIGIN,
+            confidence=1.0,
+        )
+    return TrackedRainCellOut(
+        id=cell_id,
+        state=state,  # type: ignore[arg-type]
+        current=RainCellOut(
+            id=f"{cell_id}-now",
+            timestamp="2026-08-25T04:00:00+00:00",
+            centroid=ORIGIN,
+            area_km2=12.0,
+            intensity=CellIntensityOut(min=50.0, max=70.0, mean=60.0),
+            bounds=BOUNDS,
+        ),
+        history=[],
+        motion=motion,
+        missed_frames=0,
+    )
+
+
+def _track(
+    *,
+    status: str = "ok",
+    frames_used: int = 4,
+    cells: list[TrackedRainCellOut] | None = None,
+    message: str | None = None,
+) -> RainCellTrackResponse:
+    return RainCellTrackResponse(
+        status=status,  # type: ignore[arg-type]
+        frames_used=frames_used,
+        cells=cells if cells is not None else [],
+        message=message,
+    )
+
+
+def test_engine_unavailable_passthrough():
+    track = _track(
+        status="unavailable",
+        frames_used=0,
+        cells=[_cell()],
+        message="Radar ─æang bß║úo tr├¼.",
+    )
+    result = run_nowcast(track, generated_at=GENERATED_AT)
+
+    assert result.status == "unavailable"
+    assert result.predictions == []
+    assert result.message == "Radar ─æang bß║úo tr├¼."
+    assert result.frames_used == 0
+    assert result.horizons == list(settings.nowcast_horizons_minutes)
+    assert result.model.name == settings.nowcast_model_name
+    assert result.model.version == settings.nowcast_model_version
+    assert result.radar_age_seconds is None
+    assert result.generated_at == GENERATED_AT
+
+
+def test_engine_unavailable_uses_vietnamese_default():
+    track = _track(status="unavailable", frames_used=1, message=None)
+    result = run_nowcast(track, generated_at=GENERATED_AT)
+
+    assert result.status == "unavailable"
+    assert result.predictions == []
+    assert result.message == "Dß╗» liß╗çu theo d├╡i ├┤ m╞░a tß║ím thß╗¥i kh├┤ng khß║ú dß╗Ñng."
+
+
+def test_engine_empty_cells_ok_with_message():
+    track = _track(status="ok", frames_used=3, cells=[], message=None)
+    result = run_nowcast(track, generated_at=GENERATED_AT)
+
+    assert result.status == "ok"
+    assert result.predictions == []
+    assert result.message == "Kh├┤ng c├│ ├┤ m╞░a ─æang theo d├╡i ─æß╗â dß╗▒ b├ío."
+    assert result.frames_used == 3
+    assert result.horizons == list(settings.nowcast_horizons_minutes)
+    assert result.model.name == settings.nowcast_model_name
+    assert result.model.version == settings.nowcast_model_version
+
+
+def test_engine_runs_baseline_and_sets_model_info():
+    track = _track(status="ok", frames_used=4, cells=[_cell()])
+    result = run_nowcast(track, generated_at=GENERATED_AT, radar_age_seconds=120)
+
+    assert result.status == "ok"
+    assert result.message is None
+    assert result.generated_at == GENERATED_AT
+    assert result.frames_used == 4
+    assert result.radar_age_seconds == 120
+    assert result.horizons == [5, 10, 15, 30, 60]
+    assert result.model.name == "baseline"
+    assert result.model.version == "0.1"
+    assert len(result.predictions) == 5
+    assert {p.forecast_minutes for p in result.predictions} == {5, 10, 15, 30, 60}
+    assert all(p.kind == "predicted" for p in result.predictions)
+    assert all(p.cell_id == "c1" for p in result.predictions)
+
+
+def test_engine_partial_when_track_partial():
+    track = _track(
+        status="partial",
+        frames_used=2,
+        cells=[_cell()],
+        message="Mß╗Öt sß╗æ khung radar kh├┤ng khß║ú dß╗Ñng.",
+    )
+    result = run_nowcast(track, generated_at=GENERATED_AT)
+
+    assert result.status == "partial"
+    assert result.predictions
+    assert result.message == "Mß╗Öt sß╗æ khung radar kh├┤ng khß║ú dß╗Ñng."
+    assert result.frames_used == 2
+
+
+def test_engine_partial_when_missing_motion():
+    track = _track(
+        status="ok",
+        frames_used=4,
+        cells=[_cell(speed_kmh=None, bearing_degrees=90.0)],
+    )
+    result = run_nowcast(track, generated_at=GENERATED_AT)
+
+    assert result.status == "partial"
+    assert result.predictions
+    assert any(p.confidence < 0.35 for p in result.predictions)
+    assert result.message == "Mß╗Öt sß╗æ ├┤ m╞░a thiß║┐u vector chuyß╗ân ─æß╗Öng n├¬n dß╗▒ b├ío ch╞░a ─æß║ºy ─æß╗º."
diff --git a/docs/superpowers/plans/2026-08-25-stage5-ai-nowcasting.md b/docs/superpowers/plans/2026-08-25-stage5-ai-nowcasting.md
new file mode 100644
index 0000000..1ade190
--- /dev/null
+++ b/docs/superpowers/plans/2026-08-25-stage5-ai-nowcasting.md
@@ -0,0 +1,535 @@
+# Stage 5 AI Nowcasting Engine Implementation Plan
+
+> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+
+**Goal:** Add a modular backend nowcasting pipeline with a baseline rain-cell extrapolation model (`baseline` / `0.1`), expose `POST /api/nowcasting/predict`, and visualize predicted cells on the existing map with a NOW/+5mΓÇª/+60m timeline.
+
+**Architecture:** Reuse Stage 3 `RainCellService.track_for_route` inside `NowcastingService`. `NowcastingEngine` runs a pluggable `NowcastingModel`; Stage 5 ships only `BaselineExtrapolationModel`. Frontend adds `useNowcasting` + distinct MapLibre predicted layers; Stage 1ΓÇô4 layers stay unchanged when nowcasting is off.
+
+**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest; Nuxt 4, Vue 3, TypeScript, MapLibre GL, Tailwind.
+
+**Spec:** `docs/superpowers/specs/2026-08-25-stage5-ai-nowcasting-design.md`
+
+## Global Constraints
+
+- Branch: `feat/stage5-ai-nowcasting` (already created from `main`).
+- Do **not** rewrite Stage 1ΓÇô4; do **not** create a second rain-cell tracker.
+- Input path: tracked rain cells only (not fusion segments).
+- Model identity: `name="baseline"`, `version="0.1"` ΓÇö UI must label predictions as predicted / baseline, never as live radar.
+- Horizons fixed: `[5, 10, 15, 30, 60]` minutes.
+- Empty track success ΓåÆ `status="ok"`, `predictions=[]`, clear Vietnamese `message`.
+- Track `unavailable` ΓåÆ nowcast `status="unavailable"`.
+- UI language: Vietnamese (match existing controls).
+- Git on this machine may fail `git commit` with `unknown option trailer` (Git 2.27 + wrapper). Workaround: `& "C:\Program Files\Git\bin\git.exe" commit -F <msgfile>`.
+- No new Redis/microservices/DL training.
+
+## File Structure
+
+| Path | Responsibility |
+|---|---|
+| `backend/app/engine/geo_math.py` | Add `destination_point(latlng, distance_km, bearing_deg)` |
+| `backend/app/config.py` | Nowcast model name/version, horizons, intensity max, confidence knobs |
+| `backend/app/schemas/nowcasting.py` | Request/response Pydantic models |
+| `backend/app/engine/nowcasting_models.py` | `NowcastingModel` protocol + `BaselineExtrapolationModel` |
+| `backend/app/engine/nowcasting_engine.py` | Orchestrate model ΓåÆ normalize status |
+| `backend/app/services/nowcasting_service.py` | Track then predict |
+| `backend/app/api/nowcasting.py` | `POST /api/nowcasting/predict` |
+| `backend/app/main.py` | Register nowcasting router (isolated try/except like rain-cells) |
+| `backend/tests/test_geo_math_destination.py` | destination_point tests |
+| `backend/tests/test_nowcasting_baseline.py` | Baseline algorithm tests |
+| `backend/tests/test_nowcasting_engine.py` | Engine status / empty / unavailable |
+| `backend/tests/test_nowcasting_api.py` | HTTP endpoint with mocked service |
+| `frontend/app/types/nowcasting.ts` | Client types |
+| `frontend/app/composables/useNowcasting.ts` | Fetch + horizon state |
+| `frontend/app/utils/nowcast.ts` | GeoJSON builders + intensity labels |
+| `frontend/app/components/RadarControls.vue` | Nowcasting toggle + timeline |
+| `frontend/app/components/RouteMap.vue` | Predicted layers + popup |
+| `frontend/app/pages/index.vue` | Wire composable Γåö controls Γåö map |
+| `README.md` | Stage 5 section + roadmap checkbox |
+
+---
+
+### Task 1: Geo helper + config + schemas
+
+**Files:**
+- Modify: `backend/app/engine/geo_math.py`
+- Modify: `backend/app/config.py`
+- Create: `backend/app/schemas/nowcasting.py`
+- Create: `backend/tests/test_geo_math_destination.py`
+
+**Interfaces:**
+- Produces:
+  - `destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng`
+  - Settings: `nowcast_model_name: str = "baseline"`, `nowcast_model_version: str = "0.1"`, `nowcast_horizons_minutes: list[int]` default `[5,10,15,30,60]`, `nowcast_intensity_max: float = 255.0`, `nowcast_min_frames_for_full_confidence: int = 3`
+  - Schemas: `NowcastPredictRequest`, `NowcastModelInfo`, `PredictedCellMotion`, `PredictedRainCell`, `NowcastPredictionResponse`
+
+- [ ] **Step 1: Write failing destination_point test**
+
+Create `backend/tests/test_geo_math_destination.py`:
+
+```python
+from __future__ import annotations
+
+from app.engine.geo_math import destination_point, haversine_distance_m
+from app.schemas.common import LatLng
+
+
+def test_destination_point_north_1km():
+    origin = LatLng(lat=10.0, lng=106.0)
+    dest = destination_point(origin, distance_km=1.0, bearing_degrees=0.0)
+    dist_m = haversine_distance_m(origin, dest)
+    assert abs(dist_m - 1000.0) < 15.0
+    assert dest.lat > origin.lat
+    assert abs(dest.lng - origin.lng) < 1e-4
+
+
+def test_destination_point_east_and_zero():
+    origin = LatLng(lat=10.0, lng=106.0)
+    east = destination_point(origin, distance_km=2.0, bearing_degrees=90.0)
+    assert east.lng > origin.lng
+    same = destination_point(origin, distance_km=0.0, bearing_degrees=123.0)
+    assert same.lat == origin.lat and same.lng == origin.lng
+```
+
+- [ ] **Step 2: Run test ΓÇö expect fail**
+
+Run: `cd backend; python -m pytest tests/test_geo_math_destination.py -v`  
+Expected: FAIL `ImportError` / `destination_point` missing
+
+- [ ] **Step 3: Implement destination_point + config + schemas**
+
+Add to `geo_math.py`:
+
+```python
+def destination_point(origin: LatLng, distance_km: float, bearing_degrees: float) -> LatLng:
+    """Move from origin along initial bearing by distance_km (spherical Earth)."""
+    if distance_km <= 0:
+        return LatLng(lat=origin.lat, lng=origin.lng)
+    lat1 = math.radians(origin.lat)
+    lng1 = math.radians(origin.lng)
+    brng = math.radians(bearing_degrees)
+    angular = (distance_km * 1000.0) / EARTH_RADIUS_M
+    lat2 = math.asin(
+        math.sin(lat1) * math.cos(angular)
+        + math.cos(lat1) * math.sin(angular) * math.cos(brng)
+    )
+    lng2 = lng1 + math.atan2(
+        math.sin(brng) * math.sin(angular) * math.cos(lat1),
+        math.cos(angular) - math.sin(lat1) * math.sin(lat2),
+    )
+    return LatLng(lat=math.degrees(lat2), lng=((math.degrees(lng2) + 540) % 360) - 180)
+```
+
+Append to `Settings` in `config.py`:
+
+```python
+    nowcast_model_name: str = "baseline"
+    nowcast_model_version: str = "0.1"
+    nowcast_horizons_minutes: list[int] = [5, 10, 15, 30, 60]
+    nowcast_intensity_max: float = 255.0
+    nowcast_min_frames_for_full_confidence: int = 3
+```
+
+Create `backend/app/schemas/nowcasting.py`:
+
+```python
+from __future__ import annotations
+
+from datetime import datetime
+from typing import Literal
+
+from pydantic import BaseModel, Field
+
+from app.schemas.common import LatLng
+from app.schemas.rain_cell import CellBoundsOut
+
+NowcastStatus = Literal["ok", "partial", "unavailable"]
+
+
+class NowcastPredictRequest(BaseModel):
+    geometry: list[LatLng] = Field(..., min_length=2)
+    buffer_km: float | None = Field(default=None, ge=1, le=300)
+
+
+class NowcastModelInfo(BaseModel):
+    name: str
+    version: str
+
+
+class PredictedCellMotion(BaseModel):
+    speed_kmh: float | None = None
+    bearing_degrees: float | None = None
+
+
+class PredictedRainCell(BaseModel):
+    cell_id: str
+    forecast_minutes: int
+    kind: Literal["predicted"] = "predicted"
+    centroid: LatLng
+    bounds: CellBoundsOut | None = None
+    rain_probability: float | None = Field(default=None, ge=0, le=1)
+    rain_intensity: float | None = None
+    confidence: float = Field(..., ge=0, le=1)
+    motion: PredictedCellMotion | None = None
+    source: str = "rain_cell_track+baseline"
+
+
+class NowcastPredictionResponse(BaseModel):
+    generated_at: datetime
+    status: NowcastStatus
+    model: NowcastModelInfo
+    frames_used: int
+    radar_age_seconds: int | None = None
+    horizons: list[int]
+    predictions: list[PredictedRainCell]
+    message: str | None = None
+```
+
+- [ ] **Step 4: Re-run destination tests ΓÇö expect pass**
+
+Run: `cd backend; python -m pytest tests/test_geo_math_destination.py -v`  
+Expected: PASS
+
+- [ ] **Step 5: Commit**
+
+```bash
+git add backend/app/engine/geo_math.py backend/app/config.py backend/app/schemas/nowcasting.py backend/tests/test_geo_math_destination.py
+# commit via git.exe -F if wrapper breaks
+```
+
+Message: `feat(nowcast): add geo destination helper and nowcasting schemas`
+
+---
+
+### Task 2: BaselineExtrapolationModel (TDD core)
+
+**Files:**
+- Create: `backend/app/engine/nowcasting_models.py`
+- Create: `backend/tests/test_nowcasting_baseline.py`
+
+**Interfaces:**
+- Consumes: `TrackedRainCellOut`, `destination_point`, settings horizons / intensity max
+- Produces:
+  - `class NowcastingModel(Protocol): def predict(self, cells, *, frames_used: int, radar_age_seconds: int | None, horizons: list[int]) -> list[PredictedRainCell]`
+  - `class BaselineExtrapolationModel: ...` with `name`/`version` properties
+  - Helpers used by tests: intensity trend, confidence decay (can be module-private)
+
+**Algorithm locked by tests:**
+- Eligible states: `TRACKING`, `NEW` only
+- Distance km = `speed_kmh * (forecast_minutes / 60)`
+- Missing speed or bearing ΓåÆ hold centroid/bounds; confidence Γëñ 0.35 for that cell-horizon
+- Intensity: linear slope from history means if ΓëÑ2 samples; else current mean; clamp `[0, nowcast_intensity_max]`
+- `rain_probability = clamp(intensity / nowcast_intensity_max, 0, 1)` (None if intensity None)
+- Confidence base = `motion.confidence` or `0.4`; multiply by horizon factor `max(0.25, 1 - forecast_minutes/90)`; ├ù0.7 if `frames_used < nowcast_min_frames_for_full_confidence`; ├ù0.75 if `len(history) < 2`; ├ù0.5 if missing motion vector; if `radar_age_seconds` and `> settings.radar_stale_after_seconds` ├ù0.6
+
+- [ ] **Step 1: Write failing baseline tests**
+
+Create `backend/tests/test_nowcasting_baseline.py` with fixtures building `TrackedRainCellOut` + `CellMotionOut` + history. Cover at minimum:
+
+```python
+def test_horizons_emit_five_predictions_per_cell():
+    ...
+    preds = model.predict([cell], frames_used=4, radar_age_seconds=120, horizons=[5, 10, 15, 30, 60])
+    assert sorted({p.forecast_minutes for p in preds}) == [5, 10, 15, 30, 60]
+    assert all(p.kind == "predicted" for p in preds)
+    assert all(p.cell_id == "c1" for p in preds)
+
+
+def test_projects_centroid_with_speed_and_bearing():
+    # speed 60 km/h east ΓåÆ +5 min Γëê 5 km east
+    ...
+
+
+def test_missing_velocity_holds_position_low_confidence():
+    ...
+
+
+def test_missing_direction_holds_position_low_confidence():
+    ...
+
+
+def test_intensity_extrapolates_from_history():
+    ...
+
+
+def test_intensity_fallback_without_history():
+    ...
+
+
+def test_confidence_decreases_with_horizon():
+    confs = [p.confidence for p in preds if p.cell_id == "c1"]
+    assert confs == sorted(confs, reverse=True)
+
+
+def test_stale_radar_reduces_confidence():
+    ...
+
+
+def test_short_history_reduces_confidence():
+    ...
+
+
+def test_lost_cells_omitted():
+    ...
+
+
+def test_no_cells_returns_empty():
+    assert model.predict([], frames_used=3, radar_age_seconds=60, horizons=[5, 10, 15, 30, 60]) == []
+```
+
+Use `haversine_distance_m` assertions (┬▒500 m tolerance for 5 km projection).
+
+- [ ] **Step 2: Run tests ΓÇö expect fail**
+
+Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py -v`  
+Expected: FAIL import / missing module
+
+- [ ] **Step 3: Implement `nowcasting_models.py`**
+
+Implement protocol + `BaselineExtrapolationModel` exactly matching the algorithm above. Translate bounds by the same lat/lng delta as centroid when bounds exist. Set `source="rain_cell_track+baseline"`, `motion` from input speed/bearing used.
+
+- [ ] **Step 4: Run tests ΓÇö expect pass**
+
+Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py -v`  
+Expected: all PASS
+
+- [ ] **Step 5: Commit**
+
+Message: `feat(nowcast): add baseline extrapolation model`
+
+---
+
+### Task 3: NowcastingEngine
+
+**Files:**
+- Create: `backend/app/engine/nowcasting_engine.py`
+- Create: `backend/tests/test_nowcasting_engine.py`
+
+**Interfaces:**
+- Consumes: `RainCellTrackResponse`, `BaselineExtrapolationModel` (or injected `NowcastingModel`)
+- Produces: `def run_nowcast(track: RainCellTrackResponse, *, model: NowcastingModel | None = None, generated_at: datetime | None = None) -> NowcastPredictionResponse`
+
+Status rules:
+- `track.status == "unavailable"` ΓåÆ response `unavailable`, predictions `[]`, keep track message (or Vietnamese default)
+- `track.status == "partial"` ΓåÆ response `partial` (even if predictions exist)
+- Else if any predicted cell has confidence < 0.35 due to missing motion ΓåÆ `partial` with message about incomplete motion
+- Else `ok`
+- Always set `model` from active model name/version, `horizons` from settings, `frames_used` from track
+- `radar_age_seconds`: leave `None` in Stage 5 unless easily derived; engine accepts optional override kwarg default `None`
+
+- [ ] **Step 1: Write engine tests**
+
+```python
+def test_engine_unavailable_passthrough():
+    ...
+
+def test_engine_empty_cells_ok_with_message():
+    # track ok, cells=[] ΓåÆ status ok, predictions=[], message tiß║┐ng Viß╗çt
+    ...
+
+def test_engine_runs_baseline_and_sets_model_info():
+    ...
+
+def test_engine_partial_when_track_partial():
+    ...
+```
+
+- [ ] **Step 2: Run ΓÇö expect fail**
+
+- [ ] **Step 3: Implement engine**
+
+```python
+def run_nowcast(...):
+    model = model or BaselineExtrapolationModel()
+    horizons = list(settings.nowcast_horizons_minutes)
+    info = NowcastModelInfo(name=model.name, version=model.version)
+    if track.status == "unavailable":
+        return NowcastPredictionResponse(...)
+    preds = model.predict(track.cells, frames_used=track.frames_used, radar_age_seconds=radar_age_seconds, horizons=horizons)
+    # status resolution...
+```
+
+Expose `name`/`version` properties on baseline model reading from settings.
+
+- [ ] **Step 4: Tests pass**
+
+- [ ] **Step 5: Commit**
+
+Message: `feat(nowcast): add nowcasting engine orchestrator`
+
+---
+
+### Task 4: Service + API + main registration
+
+**Files:**
+- Create: `backend/app/services/nowcasting_service.py`
+- Create: `backend/app/api/nowcasting.py`
+- Modify: `backend/app/main.py`
+- Create: `backend/tests/test_nowcasting_api.py`
+
+**Interfaces:**
+- `NowcastingService.predict_for_route(geometry, buffer_km=None) -> NowcastPredictionResponse`
+- Internally: `track = await get_rain_cell_service().track_for_route(...)` then `return run_nowcast(track)`
+- `get_nowcasting_service()` singleton like rain cells
+- Router: `@router.post("/api/nowcasting/predict", response_model=NowcastPredictionResponse)`
+
+- [ ] **Step 1: Write API test with mocked nowcasting service**
+
+Mirror `test_rain_cells_api.py`: patch `app.services.nowcasting_service._nowcasting_service` with `AsyncMock` returning a filled `NowcastPredictionResponse`, POST geometry, assert 200 + `model.name == "baseline"` + horizons + `predictions[0].kind == "predicted"`.
+
+Also add one unit-style test that `NowcastingService.predict_for_route` calls rain-cell track then engine (mock `get_rain_cell_service`).
+
+- [ ] **Step 2: Run ΓÇö expect fail**
+
+- [ ] **Step 3: Implement service + API; register in `main.py`**
+
+In `main.py`, inside the successful boot block, after rain-cells try/except, add similar:
+
+```python
+    try:
+        from app.api.nowcasting import router as nowcasting_router
+        app.include_router(nowcasting_router)
+    except Exception:
+        logging.getLogger(__name__).exception("Nowcasting router failed to load")
+```
+
+- [ ] **Step 4: Run API + engine + baseline suite**
+
+Run: `cd backend; python -m pytest tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py -v`  
+Expected: all PASS
+
+- [ ] **Step 5: Commit**
+
+Message: `feat(nowcast): expose POST /api/nowcasting/predict`
+
+---
+
+### Task 5: Frontend types + `useNowcasting`
+
+**Files:**
+- Create: `frontend/app/types/nowcasting.ts`
+- Create: `frontend/app/composables/useNowcasting.ts`
+- Create: `frontend/app/utils/nowcast.ts`
+
+**Interfaces:**
+- Mirror backend types (`NowcastPredictionResponse`, `PredictedRainCell`, horizons union)
+- `useNowcasting()` returns: `enabled`, `selectedHorizon` (`0 | 5 | 10 | 15 | 30 | 60` where `0` = NOW), `loading`, `errorMessage`, `response`, `predictionsForHorizon` computed, `setEnabled`, `setHorizon`, `fetchNowcast(geometry)`, refresh every 300s when enabled
+- `predictionsForHorizon`: filter `response.predictions` by `forecast_minutes === selectedHorizon` when horizon > 0; empty when NOW
+- `utils/nowcast.ts`: `nowcastGeoJson(cells: PredictedRainCell[])`, `intensityLabel(intensity: number | null): string`, reuse `bearingToCompass` from `rainCell.ts`
+
+- [ ] **Step 1: Add types + composable + utils** (no separate Jest in repo ΓÇö verify by TypeScript usage and manual later)
+
+`useNowcasting.ts` pattern copy from `useRainCells.ts` but endpoint `/api/nowcasting/predict` and keep `selectedHorizon` in `useState("nowcast-horizon", () => 0)`.
+
+Intensity labels (Vietnamese): null ΓåÆ `Kh├┤ng r├╡`; `<40` nhß║╣; `<90` vß╗½a; else mß║ính (thresholds aligned to RainViewer-ish scale).
+
+- [ ] **Step 2: Commit**
+
+Message: `feat(nowcast): add frontend types and useNowcasting composable`
+
+---
+
+### Task 6: RadarControls ΓÇö toggle + timeline
+
+**Files:**
+- Modify: `frontend/app/components/RadarControls.vue`
+
+**Interfaces:**
+- New props: `nowcastingEnabled`, `nowcastingLoading`, `nowcastingError`, `nowcastingModelLabel`, `selectedHorizon`, `nowcastPredictionCount`, `routeReady` (already exists)
+- Emits: `update:nowcastingEnabled`, `update:selectedHorizon`
+- When `nowcastingEnabled && routeReady`, show timeline buttons: `NOW`, `+5m`, `+10m`, `+15m`, `+30m`, `+60m`
+- Show small note: `Dß╗▒ b├ío baseline ΓÇö kh├┤ng phß║úi radar quan s├ít` + model label
+
+- [ ] **Step 1: Extend props/emits/template** following existing rain-cells toggle markup (checkbox + status lines). Horizon buttons: highlight selected with existing accent classes.
+
+- [ ] **Step 2: Commit**
+
+Message: `feat(nowcast): add nowcasting toggle and horizon timeline UI`
+
+---
+
+### Task 7: RouteMap predicted layers + inspection panel
+
+**Files:**
+- Modify: `frontend/app/components/RouteMap.vue`
+- Optionally small helper already in `utils/nowcast.ts`
+
+**Interfaces:**
+- New props: `nowcastingEnabled?: boolean`, `selectedHorizon?: number`, `predictedCells?: PredictedRainCell[]`, `nowcastModel?: { name: string; version: string } | null`
+- Layers (distinct IDs): `nowcast-bbox`, `nowcast-points` ΓÇö dashed line / teal fill opacity ~0.15, circle color `#2dd4bf`, text field `+{forecast_minutes}m` if MapLibre symbol feasible; otherwise popup only
+- Show layers only when `nowcastingEnabled && selectedHorizon > 0 && predictedCells.length`
+- Click ΓåÆ popup Vietnamese fields: Nowcasting, forecast, probability %, intensity label, confidence %, movement, model Baseline v0.1, disclaimer predicted
+- Do not reuse observed rain-cell layer IDs or colors (observed uses yellow/red)
+
+- [ ] **Step 1: Implement GeoJSON update watchers mirroring rain-cell pattern in `RouteMap.vue`**
+
+- [ ] **Step 2: Manual sanity (dev server) optional; ensure no TS errors in component
+
+- [ ] **Step 3: Commit**
+
+Message: `feat(nowcast): render predicted rain cells on map`
+
+---
+
+### Task 8: Wire `index.vue` + README
+
+**Files:**
+- Modify: `frontend/app/pages/index.vue`
+- Modify: `README.md`
+
+**Wiring:**
+- Import `useNowcasting`
+- On analyze success / geometry available: if nowcasting enabled, `fetchNowcast(geometry)` (same geometry as rain cells)
+- Pass props to `RadarControls` and `RouteMap`
+- `onRefreshLayers` also refreshes nowcast when enabled
+- README: Stage 5 section describing baseline architecture diagram (short), how to call API, how to toggle UI; mark roadmap `[x] Stage 5` only after feature works ΓÇö during this task set to `[x]` and note baseline limitations
+
+- [ ] **Step 1: Wire page**
+
+- [ ] **Step 2: Update README Stage 5**
+
+Include:
+- Architecture one-liner matching spec
+- `POST /api/nowcasting/predict`
+- Baseline Γëá trained ML
+- How to test locally (backend pytest + UI toggle)
+
+- [ ] **Step 3: Run full backend nowcast-related tests**
+
+Run: `cd backend; python -m pytest tests/test_geo_math_destination.py tests/test_nowcasting_baseline.py tests/test_nowcasting_engine.py tests/test_nowcasting_api.py tests/test_rain_cells.py tests/test_fusion_engine.py -v`  
+Expected: all PASS (Stage 3/4 unbroken)
+
+- [ ] **Step 4: Commit**
+
+Message: `feat(nowcast): wire Stage 5 UI and document baseline nowcasting`
+
+---
+
+## Spec coverage checklist (self-review)
+
+| Spec requirement | Task |
+|---|---|
+| Modular engine + model interface | 2, 3 |
+| Baseline model baseline/0.1 | 2 |
+| Reuse rain-cell tracking | 4 |
+| Horizons 5/10/15/30/60 | 1ΓÇô2 |
+| Geometry + intensity + probability + confidence | 2 |
+| `kind=predicted` + provenance | 2, 7 |
+| API endpoint | 4 |
+| Toggle + timeline UI | 6, 8 |
+| Distinct map layers + inspect panel | 7 |
+| Missing/stale handling | 2, 3 |
+| Tests listed in spec | 1ΓÇô4 |
+| Docs / ML insertion point | Spec already + README Task 8 |
+| No Stage 1ΓÇô4 rewrite | All tasks additive |
+
+## Execution Handoff
+
+Plan complete and saved to `docs/superpowers/plans/2026-08-25-stage5-ai-nowcasting.md`.
+
+**Two execution options:**
+
+1. **Subagent-Driven (recommended)** ΓÇö fresh subagent per task, review between tasks  
+2. **Inline Execution** ΓÇö execute tasks in this session with executing-plans checkpoints  
+
+Which approach?
diff --git a/docs/superpowers/specs/2026-08-25-stage5-ai-nowcasting-design.md b/docs/superpowers/specs/2026-08-25-stage5-ai-nowcasting-design.md
new file mode 100644
index 0000000..1d5870e
--- /dev/null
+++ b/docs/superpowers/specs/2026-08-25-stage5-ai-nowcasting-design.md
@@ -0,0 +1,329 @@
+# Route Weather Stage 5 ΓÇö AI Nowcasting Engine ΓÇö Design Specification
+
+> Approved: 2026-08-25  
+> Approach: **Engine + BaselineExtrapolationModel** (Approach 1)  
+> Builds on Stage 1ΓÇô4 (Route Weather MVP, Live Radar, Rain-cell Tracking, Satellite Fusion)
+
+## 1. Product Goal
+
+Stage 3ΓÇô4 answer: *"Where are rain cells now, and how are they moving / fused with other sources?"*
+
+Stage 5 begins answering: *"Where will those rain cells likely be in the next 5ΓÇô60 minutes?"*
+
+```text
+Current Weather State (observed)
+        +
+Rain-cell Tracking (Stage 3)
+        Γåô
+Nowcasting Engine
+        Γåô
+Baseline Model (extrapolation)
+        Γåô
+Future Rain Prediction
+        Γåô
+API + Map Visualization
+```
+
+The first model is a **baseline motion extrapolation**, not a trained deep-learning nowcaster. It establishes the modular pipeline so a future ML/DL model can replace the baseline without rewriting the API or frontend.
+
+## 2. Decisions Locked
+
+| Topic | Decision |
+|---|---|
+| Primary input | Tracked rain cells only (reuse Stage 3 `RainCellService`) ΓÇö not fusion segments |
+| API | New `POST /api/nowcasting/predict` with `{ geometry, buffer_km? }`; backend tracks then predicts |
+| Model architecture | Pluggable `NowcastingModel` behind `NowcastingEngine` |
+| First model | `BaselineExtrapolationModel` ΓÇö `name=baseline`, `version=0.1` |
+| Horizons | Fixed: 5, 10, 15, 30, 60 minutes |
+| UI activation | Separate ΓÇ£NowcastingΓÇ¥ toggle in `RadarControls` + timeline when ON |
+| Map | Distinct predicted layers (not identical to live radar / observed rain cells) |
+| Fusion | Do not require `/api/weather-fusion/state` for Stage 5 predict path |
+| Second tracker | Forbidden ΓÇö reuse existing rain-cell tracking |
+| Deep learning / training | Out of scope for Stage 5 |
+| Route risk / ETA impact | Out of scope |
+| Git branch | `feat/stage5-ai-nowcasting` from `main` |
+
+## 3. Existing Stage 1ΓÇô4 Context (constraints)
+
+| Item | Current state |
+|---|---|
+| Unified weather | `WeatherFusionResponse` / `FusedSegmentState` via `POST /api/weather-fusion/state` (no type named `WeatherState`) |
+| Rain cells | `POST /api/rain-cells/track` ΓåÆ `TrackedRainCellOut` with centroid, bounds, intensity, area, `motion.speed_kmh` / `bearing_degrees` / `confidence`, `history` |
+| Growth rate | Not a first-class field; may be inferred from `history` or fall back conservatively |
+| Fusion features | `SegmentNowcastFeatures` describe **present** state only ΓÇö not forecasts |
+| Frontend | Nuxt / Vue: `useRadar`, `useRainCells`, `useWeatherFusion`, `RouteMap`, `RadarControls` |
+| Map | MapLibre layers for radar, satellite, rain-cell bbox/points/motion |
+| Backend pattern | FastAPI routers; heavy work via POST + Pydantic; engines under `app/engine`, services under `app/services` |
+
+**Do not rewrite or replace Stage 1ΓÇô4.** Rain-cell and radar overlays must keep working when nowcasting is off.
+
+## 4. System Architecture
+
+```text
+Route geometry (client)
+        Γåô
+POST /api/nowcasting/predict
+        Γåô
+NowcastingService
+        Γåô
+RainCellService.track_for_route   ΓåÉ Stage 3 reuse
+        Γåô
+NowcastingEngine
+        Γåô
+NowcastingModel (protocol/interface)
+        Γåô
+BaselineExtrapolationModel (v0.1)
+        Γåô
+NowcastPredictionResponse
+        Γåô
+useNowcasting ΓåÆ RouteMap predicted layers + timeline + info panel
+```
+
+### Responsibility boundaries
+
+| Layer | Does | Does not |
+|---|---|---|
+| `RainCellService` | Detect/track cells for corridor | Future prediction |
+| `NowcastingEngine` | Select model, run predict, normalize output | Provider HTTP / tile decode |
+| `BaselineExtrapolationModel` | Extrapolate position, intensity, confidence | Call external weather APIs |
+| `NowcastingService` / API | Orchestrate request ΓåÆ response | Vue business logic |
+| `useNowcasting` | Fetch, cache state, selected horizon | Run extrapolation math |
+| `RouteMap` / controls | Draw predicted geometry; timeline; panel | Algorithms |
+
+### Future model insertion point
+
+```text
+NowcastingModel
+  Γö£ΓöÇΓöÇ BaselineExtrapolationModel   ΓåÉ Stage 5
+  Γö£ΓöÇΓöÇ MLModel                      ΓåÉ future
+  ΓööΓöÇΓöÇ DeepLearningModel            ΓåÉ future
+```
+
+Engine (or thin factory) selects the active model by config. API response always includes `model.name` + `model.version`. Frontend and API contract stay stable across model swaps.
+
+## 5. Normalized Prediction Models
+
+Adapt names to existing Pydantic / TypeScript conventions (`lat`/`lng`, snake_case in API JSON as elsewhere).
+
+### Request
+
+```typescript
+interface NowcastPredictRequest {
+  geometry: { lat: number; lng: number }[]  // min 2
+  buffer_km?: number                        // optional; same semantics as rain-cells
+}
+```
+
+### Response
+
+```typescript
+interface NowcastModelInfo {
+  name: "baseline" | string
+  version: string  // e.g. "0.1"
+}
+
+interface PredictedRainCell {
+  cell_id: string
+  forecast_minutes: 5 | 10 | 15 | 30 | 60
+  kind: "predicted"                         // never "observed"
+  centroid: { lat: number; lng: number }
+  bounds?: { north: number; south: number; east: number; west: number }
+  rain_probability: number | null           // 0ΓÇô1
+  rain_intensity: number | null             // projected mean intensity scale
+  confidence: number                        // 0ΓÇô1
+  motion?: {
+    speed_kmh: number | null
+    bearing_degrees: number | null
+  }
+  source: "rain_cell_track+baseline" | string
+  // Reserved for later without breaking clients:
+  // rain_rate?, predicted_area_km2?, uncertainty?, cell_velocity?, cell_direction?
+}
+
+interface NowcastPredictionResponse {
+  generated_at: string
+  status: "ok" | "partial" | "unavailable"
+  model: NowcastModelInfo
+  frames_used: number
+  radar_age_seconds?: number | null
+  horizons: number[]                        // [5, 10, 15, 30, 60]
+  predictions: PredictedRainCell[]
+  message?: string | null
+}
+```
+
+Provenance rules:
+
+- Every prediction item has `kind: "predicted"`.
+- UI and copy must distinguish **Observed** (radar / tracked cells) vs **Predicted** (nowcast).
+- Never present baseline output as validated scientific AI accuracy.
+
+## 6. Baseline Extrapolation Algorithm
+
+Constants:
+
+- Horizons: `[5, 10, 15, 30, 60]` minutes  
+- Model: `baseline` / `0.1`
+
+Per tracked cell eligible for prediction (`TRACKING` or `NEW` with usable `current`):
+
+1. **Position**  
+   - If `motion.speed_kmh` and `motion.bearing_degrees` present: displace centroid (and translate bounds) along great-circle / local approximation for `forecast_minutes`.  
+   - If missing velocity or direction: keep current position; reduce confidence sharply; contribute to `status=partial` when common.
+
+2. **Intensity**  
+   - If `history` has ΓëÑ 2 intensity (or area) samples: apply a simple linear trend, clamp to a safe range (e.g. ΓëÑ 0 and Γëñ configured max).  
+   - Else: keep current mean intensity (conservative fallback); do not invent growth.
+
+3. **Rain probability**  
+   - Derive a simple 0ΓÇô1 score from projected intensity and confidence (deterministic heuristic). Null only if intensity truly unavailable.
+
+4. **Confidence**  
+   Start from `motion.confidence` (or a low default if absent). Multiply / subtract for:
+   - longer horizons  
+   - short history / `NEW`  
+   - missing or unstable speed/bearing  
+   - stale radar / few `frames_used`  
+   - rapid change in area/intensity when detectable  
+   Clamp to `[0, 1]`.
+
+5. **Empty / failed track**  
+   - No cells ΓåÆ `predictions=[]` with clear `message`; prefer `status=unavailable` or `ok` with empty list + message (pick one consistently in implementation: **`unavailable` when track unavailable; `ok` with empty predictions when track succeeded but no active cells**).  
+   - Track `unavailable` ΓåÆ nowcast `unavailable`.  
+   - Never fabricate cells.
+
+`LOST` / `EXPIRED` cells are not projected as active forecasts (omit or only surface if needed for debugging ΓÇö default: **omit**).
+
+## 7. API
+
+| Method | Path | Body |
+|---|---|---|
+| POST | `/api/nowcasting/predict` | `NowcastPredictRequest` |
+
+- Register router in `main.py` similarly to rain-cells (prefer try/except isolation so Stage 5 load failure does not take down Stage 1ΓÇô2).  
+- Reuse rain-cell buffer defaults from settings when `buffer_km` omitted.  
+- Errors follow existing patterns (`503` / `502` where appropriate for upstream failure).
+
+Do **not** overload `POST /api/rain-cells/track` with predictions.
+
+## 8. Frontend Integration
+
+### Toggle & timeline
+
+- Add **Nowcasting** toggle to `RadarControls` (same interaction language as Rain cells / Radar / Satellite).  
+- When enabled and route geometry exists, `useNowcasting` calls the predict API.  
+- Show timeline:
+
+```text
+NOW ΓöÇΓöÇ +5m ΓöÇΓöÇ +10m ΓöÇΓöÇ +15m ΓöÇΓöÇ +30m ΓöÇΓöÇ +60m
+```
+
+- `NOW`: observed layers only (existing radar / rain cells behavior).  
+- Selected horizon Γëá `NOW`: show predicted layers for that horizon.
+
+### Map layers
+
+Distinct from observed rain-cell styling (e.g. dashed bounds, different hue such as teal/cyan, lower fill opacity, horizon label). Include a legend/badge: **Predicted ΓÇö Baseline v0.1**.
+
+### Info panel
+
+On selecting a predicted cell, show forecast minutes, rain probability, predicted intensity, confidence, movement (bearing + speed), and model name/version, plus a short disclaimer that data is predicted.
+
+### Composable
+
+`useNowcasting`: `enabled`, `selectedHorizon`, loading/error, response cache; refresh on route change and a polite interval (same order of magnitude as rain cells, ~5 minutes). Do not recompute predictions on every map render.
+
+Do not redesign Stage 1 `WeatherTimeline` (route ETA forecast cards).
+
+## 9. Missing / Stale Data Handling
+
+| Situation | Behavior |
+|---|---|
+| No active rain cells | Empty predictions + clear message |
+| Missing velocity / direction | Hold position; low confidence; often `partial` |
+| Insufficient history | Conservative intensity; lower confidence |
+| Stale radar / few frames | Lower confidence; may be `partial` |
+| Unstable motion | Lower confidence |
+| Track service unavailable | `status=unavailable` |
+| Missing satellite / forecast | Irrelevant to Stage 5 path (cell-only input); ignore |
+
+Never invent sensor observations.
+
+## 10. Performance
+
+- Prediction runs in backend service/engine, not in Vue render loops.  
+- Reuse Stage 3 tracking results within the same request (single track call inside `NowcastingService`).  
+- Optional light response caching only if it matches existing project patterns; do not add new infrastructure (Redis, etc.) in Stage 5.
+
+## 11. Testing
+
+Minimum backend coverage:
+
+1. Horizon generation (5/10/15/30/60)  
+2. Position projection with known speed/bearing  
+3. Missing velocity handling  
+4. Missing direction handling  
+5. Intensity extrapolation with history vs fallback  
+6. Confidence decreases with horizon  
+7. Short history / NEW cell  
+8. Stale / low `frames_used`  
+9. No rain-cell scenario  
+10. Normalized prediction fields (`kind`, model info, geometry)  
+11. API response structure (schema / endpoint with mocked service)
+
+Include realistic edge cases (zero speed, opposite bearing wrap, empty geometry rejected by validation).
+
+## 12. Documentation & Delivery
+
+- This design file is the Stage 5 architecture source of truth.  
+- README roadmap: mark Stage 5 in progress / done when implementation lands.  
+- Implementation plan follows after this spec is user-reviewed.
+
+## 13. Out of Scope / Non-goals
+
+- Rewriting Stage 1ΓÇô4  
+- Second rain-cell tracker  
+- Training neural networks / large ML pipelines  
+- Claiming calibrated scientific accuracy  
+- Microservices split  
+- New dashboards beyond toggle + timeline + panel  
+- Fake historical training data  
+- Binding nowcast into route risk scoring / ETA (future stage)
+
+## 14. Acceptance Criteria
+
+Stage 5 is complete when:
+
+- [ ] Stage 1ΓÇô4 behavior still works with nowcasting off  
+- [ ] Modular `NowcastingEngine` + `NowcastingModel` interface exist  
+- [ ] `BaselineExtrapolationModel` (`baseline` / `0.1`) exists  
+- [ ] Tracked cells project to 5/10/15/30/60 minutes with geometry  
+- [ ] Predictions include probability/intensity/confidence and `kind=predicted`  
+- [ ] `POST /api/nowcasting/predict` returns normalized response  
+- [ ] Frontend toggle + timeline update map by horizon  
+- [ ] Predicted cells are inspectable and visually distinct from observations  
+- [ ] Missing/stale data handled without fabrication  
+- [ ] Core prediction logic has tests  
+- [ ] Architecture documents where a real ML model plugs in later  
+
+## 15. Files Likely Touched (implementation preview)
+
+**Backend (new):**  
+`schemas/nowcasting.py`, `engine/nowcasting_models.py` (protocol + baseline), `engine/nowcasting_engine.py`, `services/nowcasting_service.py`, `api/nowcasting.py`, `tests/test_nowcasting*.py`
+
+**Backend (modify):**  
+`main.py` (router registration), possibly `config.py` for horizons / model name defaults
+
+**Frontend (new/modify):**  
+`composables/useNowcasting.ts`, `types/nowcasting.ts`, `RadarControls.vue`, `RouteMap.vue`, `pages/index.vue`, small utils for predicted GeoJSON
+
+**Docs:**  
+this spec; README Stage 5 note
+
+## 16. Known Limitations (accepted)
+
+- Baseline advection only; no convective initiation/decay physics beyond simple intensity trend  
+- Growth/decay from short RainViewer history is weak  
+- Confidence is heuristic, not probability-calibrated  
+- Corridor / route-scoped cells only ΓÇö not full-domain nowcasting  
+- Visual prediction Γëá meteorological verification product
diff --git a/frontend/app/components/RadarControls.vue b/frontend/app/components/RadarControls.vue
index cff98ff..ce25001 100644
--- a/frontend/app/components/RadarControls.vue
+++ b/frontend/app/components/RadarControls.vue
@@ -31,10 +31,54 @@
         {{ rainCellCount }} v├╣ng m╞░a ─æang theo d├╡i
         <span v-if="rainCellsFramesUsed"> ┬╖ {{ rainCellsFramesUsed }} khung radar</span>
       </div>
     </div>
 
+    <label class="flex cursor-pointer items-center gap-2">
+      <input
+        type="checkbox"
+        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
+        :checked="nowcastingEnabled"
+        :disabled="!routeReady"
+        @change="onNowcastingToggle"
+      />
+      <span :class="routeReady ? '' : 'text-slate-500'">Nowcasting (dß╗▒ b├ío m╞░a)</span>
+    </label>
+    <p v-if="!routeReady" class="text-[10px] text-slate-500">Cß║ºn c├│ lß╗Ö tr├¼nh ─æß╗â dß╗▒ b├ío m╞░a.</p>
+
+    <div v-if="nowcastingEnabled && routeReady" class="space-y-2">
+      <div class="space-y-1 text-xs">
+        <div v-if="nowcastingLoading" class="text-slate-400">─Éang dß╗▒ b├ío m╞░aΓÇª</div>
+        <div v-else-if="nowcastingError" class="text-amber-400">{{ nowcastingError }}</div>
+        <div v-else-if="nowcastPredictionCount !== null" class="text-slate-300">
+          {{ nowcastPredictionCount }} v├╣ng m╞░a dß╗▒ b├ío
+        </div>
+      </div>
+
+      <div class="flex flex-wrap gap-1">
+        <button
+          v-for="option in horizonOptions"
+          :key="option.value"
+          type="button"
+          class="rounded border px-2 py-0.5 text-[11px] font-medium"
+          :class="
+            selectedHorizon === option.value
+              ? 'border-blue-500 bg-blue-500/20 text-blue-400'
+              : 'border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-200'
+          "
+          @click="$emit('update:selectedHorizon', option.value)"
+        >
+          {{ option.label }}
+        </button>
+      </div>
+
+      <p class="text-[10px] text-slate-500">
+        Dß╗▒ b├ío baseline ΓÇö kh├┤ng phß║úi radar quan s├ít
+        <span v-if="nowcastingModelLabel"> ┬╖ {{ nowcastingModelLabel }}</span>
+      </p>
+    </div>
+
     <label class="flex cursor-pointer items-center gap-2">
       <input
         type="checkbox"
         class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
         :checked="enabled"
@@ -122,10 +166,11 @@
     </div>
   </div>
 </template>
 
 <script setup lang="ts">
+import type { NowcastSelectedHorizon } from "~/types/nowcasting"
 import type { RadarFrameResponse, RadarLegend } from "~/types/radar"
 
 const props = defineProps<{
   enabled: boolean
   opacity: number
@@ -145,21 +190,38 @@ const props = defineProps<{
   satelliteLoading: boolean
   satelliteErrorMessage: string | null
   satelliteStatus: "ok" | "stale" | "unavailable" | null
   satelliteFreshnessLabel: string | null
   satelliteTimestampDisplay: string | null
+  nowcastingEnabled: boolean
+  nowcastingLoading: boolean
+  nowcastingError: string | null
+  nowcastingModelLabel: string | null
+  selectedHorizon: NowcastSelectedHorizon
+  nowcastPredictionCount: number | null
 }>()
 
 const emit = defineEmits<{
   "update:enabled": [value: boolean]
   "update:opacity": [value: number]
   "update:rainCellsEnabled": [value: boolean]
   "update:satelliteEnabled": [value: boolean]
   "update:satelliteOpacity": [value: number]
+  "update:nowcastingEnabled": [value: boolean]
+  "update:selectedHorizon": [value: NowcastSelectedHorizon]
   refresh: []
 }>()
 
+const horizonOptions: { value: NowcastSelectedHorizon; label: string }[] = [
+  { value: 0, label: "NOW" },
+  { value: 5, label: "+5m" },
+  { value: 10, label: "+10m" },
+  { value: 15, label: "+15m" },
+  { value: 30, label: "+30m" },
+  { value: 60, label: "+60m" },
+]
+
 const legend = computed<RadarLegend | null>(() => props.frame?.legend ?? null)
 
 const statusClass = computed(() => {
   if (props.frame?.status === "stale") return "text-amber-400"
   if (props.frame?.status === "ok") return "text-green-400"
@@ -182,10 +244,14 @@ function onOpacity(event: Event) {
 
 function onRainCellsToggle(event: Event) {
   emit("update:rainCellsEnabled", (event.target as HTMLInputElement).checked)
 }
 
+function onNowcastingToggle(event: Event) {
+  emit("update:nowcastingEnabled", (event.target as HTMLInputElement).checked)
+}
+
 function onSatelliteToggle(event: Event) {
   emit("update:satelliteEnabled", (event.target as HTMLInputElement).checked)
 }
 
 function onSatelliteOpacity(event: Event) {
diff --git a/frontend/app/components/RouteMap.vue b/frontend/app/components/RouteMap.vue
index b953434..348eefa 100644
--- a/frontend/app/components/RouteMap.vue
+++ b/frontend/app/components/RouteMap.vue
@@ -4,11 +4,13 @@
 
 <script setup lang="ts">
 import type maplibregl from "maplibre-gl"
 import type { RouteWeatherResponse } from "~/types/routeWeather"
 import type { TrackedRainCell } from "~/types/rainCell"
+import type { NowcastModelInfo, PredictedRainCell } from "~/types/nowcasting"
 import { bearingToCompass } from "~/utils/rainCell"
+import { formatNowcastPopup, nowcastGeoJson } from "~/utils/nowcast"
 
 const props = defineProps<{
   routeWeather: RouteWeatherResponse | null
   radarEnabled?: boolean
   radarOpacity?: number
@@ -18,10 +20,14 @@ const props = defineProps<{
   satelliteOpacity?: number
   satelliteTileUrl?: string | null
   satelliteTileMaxZoom?: number
   rainCellsEnabled?: boolean
   trackedCells?: TrackedRainCell[]
+  nowcastingEnabled?: boolean
+  selectedHorizon?: number
+  predictedCells?: PredictedRainCell[]
+  nowcastModel?: NowcastModelInfo | null
 }>()
 
 const config = useRuntimeConfig()
 const mapEl = ref<HTMLElement | null>(null)
 const map = shallowRef<maplibregl.Map | null>(null)
@@ -42,12 +48,21 @@ const RAIN_CELLS_POINTS_SOURCE = "rain-cells-points"
 const RAIN_CELLS_BBOX_SOURCE = "rain-cells-bbox"
 const RAIN_CELLS_MOTION_SOURCE = "rain-cells-motion"
 const RAIN_CELLS_BBOX_LAYER = "rain-cells-bbox"
 const RAIN_CELLS_POINT_LAYER = "rain-cells-points"
 const RAIN_CELLS_MOTION_LAYER = "rain-cells-motion"
+const NOWCAST_BBOX_SOURCE = "nowcast-bbox"
+const NOWCAST_POINTS_SOURCE = "nowcast-points"
+const NOWCAST_BBOX_FILL_LAYER = "nowcast-bbox-fill"
+const NOWCAST_BBOX_LAYER = "nowcast-bbox"
+const NOWCAST_POINT_LAYER = "nowcast-points"
+const NOWCAST_POINT_LABEL_LAYER = "nowcast-points-label"
+const NOWCAST_TEAL = "#2dd4bf"
 
 let rainCellPopup: maplibregl.Popup | null = null
+let nowcastPopup: maplibregl.Popup | null = null
+let nowcastClickBound = false
 
 async function ensureMap() {
   if (!process.client || map.value || !mapEl.value) return
   maplibreModule = await import("maplibre-gl")
   await import("maplibre-gl/dist/maplibre-gl.css")
@@ -378,10 +393,145 @@ function syncRainCellLayers() {
       m.getCanvas().style.cursor = ""
     })
   }
 }
 
+function visibleNowcastCells(): PredictedRainCell[] {
+  if (!props.nowcastingEnabled || (props.selectedHorizon ?? 0) <= 0) return []
+  const horizon = props.selectedHorizon
+  return (props.predictedCells ?? []).filter((c) => c.forecast_minutes === horizon)
+}
+
+function removeNowcastLayers(m: maplibregl.Map) {
+  if (m.getLayer(NOWCAST_POINT_LABEL_LAYER)) m.removeLayer(NOWCAST_POINT_LABEL_LAYER)
+  if (m.getLayer(NOWCAST_POINT_LAYER)) m.removeLayer(NOWCAST_POINT_LAYER)
+  if (m.getSource(NOWCAST_POINTS_SOURCE)) m.removeSource(NOWCAST_POINTS_SOURCE)
+  if (m.getLayer(NOWCAST_BBOX_LAYER)) m.removeLayer(NOWCAST_BBOX_LAYER)
+  if (m.getLayer(NOWCAST_BBOX_FILL_LAYER)) m.removeLayer(NOWCAST_BBOX_FILL_LAYER)
+  if (m.getSource(NOWCAST_BBOX_SOURCE)) m.removeSource(NOWCAST_BBOX_SOURCE)
+  nowcastPopup?.remove()
+}
+
+function bindNowcastLayerEvents(m: maplibregl.Map) {
+  if (nowcastClickBound) return
+  nowcastClickBound = true
+  const clickLayers = [NOWCAST_POINT_LAYER, NOWCAST_POINT_LABEL_LAYER, NOWCAST_BBOX_FILL_LAYER, NOWCAST_BBOX_LAYER]
+  for (const layerId of clickLayers) {
+    m.on("click", layerId, (e) => {
+      const f = e.features?.[0]
+      if (!f?.properties || !e.lngLat) return
+      if (!nowcastPopup) {
+        nowcastPopup = new maplibreModule!.Popup({
+          closeButton: true,
+          maxWidth: "280px",
+          className: "nowcast-popup",
+        })
+      }
+      nowcastPopup
+        .setLngLat(e.lngLat)
+        .setHTML(formatNowcastPopup(f.properties as Record<string, unknown>, props.nowcastModel))
+        .addTo(m)
+      styleRainCellPopupElement(nowcastPopup)
+    })
+    m.on("mouseenter", layerId, () => {
+      m.getCanvas().style.cursor = "pointer"
+    })
+    m.on("mouseleave", layerId, () => {
+      m.getCanvas().style.cursor = ""
+    })
+  }
+}
+
+function syncNowcastLayers() {
+  if (!map.value || !maplibreModule) return
+  const m = map.value
+  const cells = visibleNowcastCells()
+  const show = cells.length > 0
+
+  if (!show) {
+    removeNowcastLayers(m)
+    return
+  }
+
+  const gj = nowcastGeoJson(cells)
+  const beforeRoute = m.getLayer(ROUTE_LAYER) ? ROUTE_LAYER : firstSymbolLayerId(m)
+
+  if (m.getSource(NOWCAST_BBOX_SOURCE)) {
+    ;(m.getSource(NOWCAST_BBOX_SOURCE) as maplibregl.GeoJSONSource).setData(gj.bbox)
+  } else {
+    m.addSource(NOWCAST_BBOX_SOURCE, { type: "geojson", data: gj.bbox })
+    m.addLayer(
+      {
+        id: NOWCAST_BBOX_FILL_LAYER,
+        type: "fill",
+        source: NOWCAST_BBOX_SOURCE,
+        paint: {
+          "fill-color": NOWCAST_TEAL,
+          "fill-opacity": 0.15,
+        },
+      },
+      beforeRoute ?? undefined,
+    )
+    m.addLayer(
+      {
+        id: NOWCAST_BBOX_LAYER,
+        type: "line",
+        source: NOWCAST_BBOX_SOURCE,
+        paint: {
+          "line-color": NOWCAST_TEAL,
+          "line-width": 2,
+          "line-opacity": 0.85,
+          "line-dasharray": [2, 2],
+        },
+      },
+      beforeRoute ?? undefined,
+    )
+  }
+
+  if (m.getSource(NOWCAST_POINTS_SOURCE)) {
+    ;(m.getSource(NOWCAST_POINTS_SOURCE) as maplibregl.GeoJSONSource).setData(gj.points)
+  } else {
+    m.addSource(NOWCAST_POINTS_SOURCE, { type: "geojson", data: gj.points })
+    m.addLayer(
+      {
+        id: NOWCAST_POINT_LAYER,
+        type: "circle",
+        source: NOWCAST_POINTS_SOURCE,
+        paint: {
+          "circle-radius": 7,
+          "circle-color": NOWCAST_TEAL,
+          "circle-stroke-width": 2,
+          "circle-stroke-color": "#0f172a",
+        },
+      },
+      beforeRoute ?? undefined,
+    )
+    m.addLayer(
+      {
+        id: NOWCAST_POINT_LABEL_LAYER,
+        type: "symbol",
+        source: NOWCAST_POINTS_SOURCE,
+        layout: {
+          "text-field": ["concat", "+", ["to-string", ["get", "forecast_minutes"]], "m"],
+          "text-size": 11,
+          "text-offset": [0, 1.15],
+          "text-anchor": "top",
+          "text-allow-overlap": true,
+        },
+        paint: {
+          "text-color": "#99f6e4",
+          "text-halo-color": "#0f172a",
+          "text-halo-width": 1.2,
+        },
+      },
+      beforeRoute ?? undefined,
+    )
+  }
+
+  bindNowcastLayerEvents(m)
+}
+
 function renderRouteLayers() {
   if (!map.value || !maplibreModule || !props.routeWeather) return
   const m = map.value
   const data = props.routeWeather
 
@@ -467,10 +617,11 @@ function renderRouteLayers() {
 
 function renderAll() {
   syncSatelliteLayer()
   syncRadarLayer()
   syncRainCellLayers()
+  syncNowcastLayers()
   if (props.routeWeather) renderRouteLayers()
 }
 
 watch(
   () => [props.radarEnabled, props.radarOpacity, props.radarTileUrl, props.radarTileMaxZoom] as const,
@@ -506,10 +657,20 @@ watch(
     else map.value.once("load", renderAll)
   },
   { deep: true },
 )
 
+watch(
+  () => [props.nowcastingEnabled, props.selectedHorizon, props.predictedCells] as const,
+  () => {
+    if (!map.value) return
+    if (map.value.isStyleLoaded()) syncNowcastLayers()
+    else map.value.once("load", renderAll)
+  },
+  { deep: true },
+)
+
 watch(
   () => props.routeWeather,
   async () => {
     await ensureMap()
     if (!props.routeWeather || !map.value) return
@@ -526,27 +687,33 @@ onMounted(async () => {
 })
 
 onBeforeUnmount(() => {
   startMarker?.remove()
   endMarker?.remove()
+  rainCellPopup?.remove()
+  nowcastPopup?.remove()
+  nowcastClickBound = false
   map.value?.remove()
   map.value = null
 })
 </script>
 
 <style>
 /* Load after maplibre-gl.css ΓÇö rain-cell popup must not inherit app light text on white popup shell */
-.maplibregl-popup.rain-cell-popup .maplibregl-popup-content {
+.maplibregl-popup.rain-cell-popup .maplibregl-popup-content,
+.maplibregl-popup.nowcast-popup .maplibregl-popup-content {
   background: #1e293b !important;
   color: #e2e8f0 !important;
   border-radius: 8px !important;
   box-shadow: 0 8px 24px rgba(15, 23, 42, 0.45) !important;
 }
 
-.maplibregl-popup.rain-cell-popup .maplibregl-popup-tip {
+.maplibregl-popup.rain-cell-popup .maplibregl-popup-tip,
+.maplibregl-popup.nowcast-popup .maplibregl-popup-tip {
   border-top-color: #1e293b !important;
 }
 
-.maplibregl-popup.rain-cell-popup .maplibregl-popup-close-button {
+.maplibregl-popup.rain-cell-popup .maplibregl-popup-close-button,
+.maplibregl-popup.nowcast-popup .maplibregl-popup-close-button {
   color: #94a3b8 !important;
 }
 </style>
diff --git a/frontend/app/composables/useNowcasting.ts b/frontend/app/composables/useNowcasting.ts
new file mode 100644
index 0000000..febd638
--- /dev/null
+++ b/frontend/app/composables/useNowcasting.ts
@@ -0,0 +1,105 @@
+import type { LatLng } from "~/types/routeWeather"
+import type {
+  NowcastPredictionResponse,
+  NowcastSelectedHorizon,
+  PredictedRainCell,
+} from "~/types/nowcasting"
+
+export function useNowcasting() {
+  const config = useRuntimeConfig()
+  const enabled = useState("nowcast-enabled", () => false)
+  const selectedHorizon = useState<NowcastSelectedHorizon>("nowcast-horizon", () => 0)
+  const loading = ref(false)
+  const errorMessage = ref<string | null>(null)
+  const response = ref<NowcastPredictionResponse | null>(null)
+
+  let refreshTimer: ReturnType<typeof setInterval> | null = null
+
+  function clearRefreshTimer() {
+    if (refreshTimer) {
+      clearInterval(refreshTimer)
+      refreshTimer = null
+    }
+  }
+
+  function scheduleRefresh(intervalSeconds: number) {
+    clearRefreshTimer()
+    if (!enabled.value) return
+    refreshTimer = setInterval(() => {
+      void fetchNowcast(lastGeometry.value, { silent: true })
+    }, intervalSeconds * 1000)
+  }
+
+  const lastGeometry = ref<LatLng[] | null>(null)
+
+  async function fetchNowcast(geometry: LatLng[] | null, options: { silent?: boolean } = {}) {
+    if (!enabled.value || !geometry || geometry.length < 2) {
+      response.value = null
+      return
+    }
+
+    lastGeometry.value = geometry
+    if (!options.silent) loading.value = true
+    if (!options.silent) errorMessage.value = null
+
+    try {
+      const data = await $fetch<NowcastPredictionResponse>(
+        `${config.public.apiBaseUrl}/api/nowcasting/predict`,
+        {
+          method: "POST",
+          body: { geometry },
+        },
+      )
+      response.value = data
+
+      if (data.status === "unavailable") {
+        errorMessage.value = data.message ?? "Kh├┤ng thß╗â dß╗▒ b├ío m╞░a."
+      } else {
+        errorMessage.value = data.status === "partial" ? (data.message ?? null) : null
+        scheduleRefresh(300)
+      }
+    } catch {
+      response.value = null
+      errorMessage.value = "Kh├┤ng thß╗â dß╗▒ b├ío m╞░a."
+    } finally {
+      if (!options.silent) loading.value = false
+    }
+  }
+
+  function setEnabled(value: boolean) {
+    enabled.value = value
+    if (!value) {
+      clearRefreshTimer()
+      response.value = null
+      errorMessage.value = null
+      lastGeometry.value = null
+    } else if (lastGeometry.value) {
+      void fetchNowcast(lastGeometry.value)
+    }
+  }
+
+  function setHorizon(value: NowcastSelectedHorizon) {
+    selectedHorizon.value = value
+  }
+
+  const predictionsForHorizon = computed<PredictedRainCell[]>(() => {
+    if (selectedHorizon.value === 0) return []
+    return (response.value?.predictions ?? []).filter(
+      (p) => p.forecast_minutes === selectedHorizon.value,
+    )
+  })
+
+  onBeforeUnmount(() => clearRefreshTimer())
+
+  return {
+    enabled,
+    selectedHorizon,
+    loading,
+    errorMessage,
+    response,
+    predictionsForHorizon,
+    fetchNowcast,
+    setEnabled,
+    setHorizon,
+  }
+}
diff --git a/frontend/app/pages/index.vue b/frontend/app/pages/index.vue
index d1bd37d..1d760af 100644
--- a/frontend/app/pages/index.vue
+++ b/frontend/app/pages/index.vue
@@ -41,10 +41,16 @@
         :rain-cells-enabled="rainCellsEnabled"
         :rain-cells-loading="rainCellsLoading"
         :rain-cells-error="rainCellsError"
         :rain-cell-count="rainCellCountDisplay"
         :rain-cells-frames-used="rainCellsFramesUsed"
+        :nowcasting-enabled="nowcastingEnabled"
+        :nowcasting-loading="nowcastingLoading"
+        :nowcasting-error="nowcastingError"
+        :nowcasting-model-label="nowcastingModelLabel"
+        :selected-horizon="selectedHorizon"
+        :nowcast-prediction-count="nowcastPredictionCountDisplay"
         :route-ready="routeReady"
         :satellite-enabled="satelliteEnabled"
         :satellite-opacity="satelliteOpacity"
         :satellite-loading="satelliteLoading"
         :satellite-error-message="satelliteError"
@@ -52,10 +58,12 @@
         :satellite-freshness-label="satelliteFreshness"
         :satellite-timestamp-display="satelliteTimestamp"
         @update:enabled="setRadarEnabled"
         @update:opacity="setRadarOpacity"
         @update:rain-cells-enabled="setRainCellsEnabled"
+        @update:nowcasting-enabled="setNowcastingEnabled"
+        @update:selected-horizon="setHorizon"
         @update:satellite-enabled="setSatelliteEnabled"
         @update:satellite-opacity="setSatelliteOpacity"
         @refresh="onRefreshLayers"
       />
 
@@ -86,22 +94,28 @@
             :satellite-opacity="satelliteOpacity"
             :satellite-tile-url="satelliteTileUrl"
             :satellite-tile-max-zoom="satelliteTileMaxZoom"
             :rain-cells-enabled="rainCellsEnabled"
             :tracked-cells="trackedCells"
+            :nowcasting-enabled="nowcastingEnabled"
+            :selected-horizon="selectedHorizon"
+            :predicted-cells="predictionsForHorizon"
+            :nowcast-model="nowcastResponse?.model ?? null"
           />
         </ClientOnly>
       </div>
       <WeatherTimeline :points="routeWeather?.timeline ?? []" />
     </main>
   </div>
 </template>
 
 <script setup lang="ts">
+import { useNowcasting } from "~/composables/useNowcasting"
 import { useRainCells } from "~/composables/useRainCells"
 import { useSatellite } from "~/composables/useSatellite"
 import { useWeatherFusion } from "~/composables/useWeatherFusion"
+import { nowcastModelLabel } from "~/utils/nowcast"
 
 const {
   healthOk,
   loading,
   loadingMessage,
@@ -144,10 +158,22 @@ const {
   response: rainCellsResponse,
   fetchRainCells,
   setEnabled: setRainCellsEnabled,
 } = useRainCells()
 
+const {
+  enabled: nowcastingEnabled,
+  selectedHorizon,
+  loading: nowcastingLoading,
+  errorMessage: nowcastingError,
+  response: nowcastResponse,
+  predictionsForHorizon,
+  fetchNowcast,
+  setEnabled: setNowcastingEnabled,
+  setHorizon,
+} = useNowcasting()
+
 const {
   enabled: satelliteEnabled,
   opacity: satelliteOpacity,
   loading: satelliteLoading,
   errorMessage: satelliteError,
@@ -173,17 +199,28 @@ const routeGeometry = computed(() => {
 })
 
 const routeReady = computed(() => (routeGeometry.value?.length ?? 0) >= 2)
 const rainCellCountDisplay = computed(() => (rainCellsEnabled.value && routeReady.value ? cellCount.value : null))
 const rainCellsFramesUsed = computed(() => rainCellsResponse.value?.frames_used ?? null)
+const nowcastingModelLabel = computed(() =>
+  nowcastResponse.value?.model ? nowcastModelLabel(nowcastResponse.value.model) : null,
+)
+const nowcastPredictionCountDisplay = computed(() => {
+  if (!nowcastingEnabled.value || !routeReady.value) return null
+  const preds = nowcastResponse.value?.predictions ?? []
+  return new Set(preds.map((p) => p.cell_id)).size
+})
 
 function onRefreshLayers() {
   void fetchRadar()
   void fetchSatellite()
   if (rainCellsEnabled.value && routeGeometry.value) {
     void fetchRainCells(routeGeometry.value)
   }
+  if (nowcastingEnabled.value && routeGeometry.value) {
+    void fetchNowcast(routeGeometry.value)
+  }
   if (fusionCanRefresh.value) {
     void refreshFusionDebug()
   }
 }
 
@@ -191,10 +228,16 @@ watch([routeGeometry, rainCellsEnabled], ([geom, enabled]) => {
   if (enabled && geom && geom.length >= 2) {
     void fetchRainCells(geom)
   }
 })
 
+watch([routeGeometry, nowcastingEnabled], ([geom, enabled]) => {
+  if (enabled && geom && geom.length >= 2) {
+    void fetchNowcast(geom)
+  }
+})
+
 const radarTileUrl = computed(() =>
   radarEnabled.value && radarFrame.value?.tile_url_template ? radarFrame.value.tile_url_template : null,
 )
 const radarTileMaxZoom = computed(() => radarFrame.value?.tile_max_zoom ?? 7)
 const satelliteTileUrl = computed(() =>
diff --git a/frontend/app/types/nowcasting.ts b/frontend/app/types/nowcasting.ts
new file mode 100644
index 0000000..82784ac
--- /dev/null
+++ b/frontend/app/types/nowcasting.ts
@@ -0,0 +1,45 @@
+import type { LatLng } from "~/types/routeWeather"
+import type { CellBounds } from "~/types/rainCell"
+
+export type NowcastHorizon = 5 | 10 | 15 | 30 | 60
+export type NowcastSelectedHorizon = 0 | NowcastHorizon
+export type NowcastStatus = "ok" | "partial" | "unavailable"
+
+export type NowcastModelInfo = {
+  name: string
+  version: string
+}
+
+export type PredictedCellMotion = {
+  speed_kmh?: number | null
+  bearing_degrees?: number | null
+}
+
+export type PredictedRainCell = {
+  cell_id: string
+  forecast_minutes: NowcastHorizon
+  kind: "predicted"
+  centroid: LatLng
+  bounds?: CellBounds | null
+  rain_probability: number | null
+  rain_intensity: number | null
+  confidence: number
+  motion?: PredictedCellMotion | null
+  source: string
+}
+
+export type NowcastPredictionResponse = {
+  generated_at: string
+  status: NowcastStatus
+  model: NowcastModelInfo
+  frames_used: number
+  radar_age_seconds?: number | null
+  horizons: number[]
+  predictions: PredictedRainCell[]
+  message?: string | null
+}
+
+export type NowcastPredictRequest = {
+  geometry: LatLng[]
+  buffer_km?: number | null
+}
diff --git a/frontend/app/utils/nowcast.ts b/frontend/app/utils/nowcast.ts
new file mode 100644
index 0000000..90e754a
--- /dev/null
+++ b/frontend/app/utils/nowcast.ts
@@ -0,0 +1,125 @@
+import type { NowcastModelInfo, PredictedRainCell } from "~/types/nowcasting"
+import { bearingToCompass } from "~/utils/rainCell"
+
+export function intensityLabel(intensity: number | null): string {
+  if (intensity == null) return "Kh├┤ng r├╡"
+  if (intensity < 40) return "nhß║╣"
+  if (intensity < 90) return "vß╗½a"
+  return "mß║ính"
+}
+
+export function nowcastModelLabel(model?: NowcastModelInfo | null): string {
+  if (!model) return "Baseline v0.1"
+  const name = model.name.toLowerCase() === "baseline" ? "Baseline" : model.name
+  return `${name} v${model.version}`
+}
+
+function nowcastFeatureProperties(c: PredictedRainCell) {
+  return {
+    cell_id: c.cell_id,
+    forecast_minutes: c.forecast_minutes,
+    kind: c.kind,
+    rain_probability: c.rain_probability,
+    rain_intensity: c.rain_intensity,
+    intensity_label: intensityLabel(c.rain_intensity),
+    confidence: c.confidence,
+    speed_kmh: c.motion?.speed_kmh ?? null,
+    bearing: c.motion?.bearing_degrees ?? null,
+    bearing_compass:
+      c.motion?.bearing_degrees != null ? bearingToCompass(c.motion.bearing_degrees) : null,
+    source: c.source,
+  }
+}
+
+function percentLabel(value: unknown): string | null {
+  if (value == null || value === "") return null
+  const n = Number(value)
+  if (Number.isNaN(n)) return null
+  return `${Math.round(n * 100)}%`
+}
+
+export function formatNowcastPopup(
+  featureProps: Record<string, unknown>,
+  model?: NowcastModelInfo | null,
+): string {
+  const lineStyle = 'style="color:#e2e8f0;margin:0 0 4px 0"'
+  const lines: string[] = [`<p ${lineStyle}><strong style="color:#5eead4">Nowcasting</strong></p>`]
+
+  if (featureProps.forecast_minutes != null && featureProps.forecast_minutes !== "") {
+    lines.push(`<p ${lineStyle}>Dß╗▒ b├ío: +${Number(featureProps.forecast_minutes)} ph├║t</p>`)
+  }
+
+  const probability = percentLabel(featureProps.rain_probability)
+  lines.push(
+    `<p ${lineStyle}>X├íc suß║Ñt m╞░a: ${probability ?? "Kh├┤ng r├╡"}</p>`,
+  )
+
+  const intensity =
+    (typeof featureProps.intensity_label === "string" && featureProps.intensity_label) ||
+    intensityLabel(featureProps.rain_intensity != null ? Number(featureProps.rain_intensity) : null)
+  lines.push(`<p ${lineStyle}>C╞░ß╗¥ng ─æß╗Ö: ${intensity}</p>`)
+
+  const confidence = percentLabel(featureProps.confidence)
+  lines.push(`<p ${lineStyle}>─Éß╗Ö tin cß║¡y: ${confidence ?? "Kh├┤ng r├╡"}</p>`)
+
+  if (featureProps.speed_kmh != null || featureProps.bearing != null) {
+    const parts: string[] = []
+    if (featureProps.bearing != null) {
+      const compass =
+        typeof featureProps.bearing_compass === "string" && featureProps.bearing_compass
+          ? featureProps.bearing_compass
+          : bearingToCompass(Number(featureProps.bearing))
+      parts.push(compass)
+    }
+    if (featureProps.speed_kmh != null) {
+      parts.push(`${Number(featureProps.speed_kmh).toFixed(0)} km/h`)
+    }
+    lines.push(`<p ${lineStyle}>Di chuyß╗ân: ${parts.join(" ┬╖ ")}</p>`)
+  } else {
+    lines.push(`<p ${lineStyle}>Di chuyß╗ân: kh├┤ng r├╡</p>`)
+  }
+
+  lines.push(`<p ${lineStyle}>M├┤ h├¼nh: ${nowcastModelLabel(model)}</p>`)
+  lines.push(
+    '<p style="color:#94a3b8;font-size:11px;margin:6px 0 0 0">Dß╗» liß╗çu dß╗▒ b├ío ΓÇö kh├┤ng phß║úi radar quan s├ít</p>',
+  )
+  return `<div style="color:#e2e8f0;font-size:13px;line-height:1.45">${lines.join("")}</div>`
+}
+
+export function nowcastGeoJson(cells: PredictedRainCell[]) {
+  const bboxFeatures = cells
+    .filter((c) => c.bounds)
+    .map((c) => {
+      const b = c.bounds!
+      return {
+        type: "Feature" as const,
+        geometry: {
+          type: "Polygon" as const,
+          coordinates: [
+            [
+              [b.west, b.north],
+              [b.east, b.north],
+              [b.east, b.south],
+              [b.west, b.south],
+              [b.west, b.north],
+            ],
+          ],
+        },
+        properties: nowcastFeatureProperties(c),
+      }
+    })
+
+  const pointFeatures = cells.map((c) => ({
+    type: "Feature" as const,
+    geometry: {
+      type: "Point" as const,
+      coordinates: [c.centroid.lng, c.centroid.lat],
+    },
+    properties: nowcastFeatureProperties(c),
+  }))
+
+  return {
+    bbox: { type: "FeatureCollection" as const, features: bboxFeatures },
+    points: { type: "FeatureCollection" as const, features: pointFeatures },
+  }
+}

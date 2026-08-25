# Review package Task 8
BASE: ea673cc72fe464aa378fa2bb3c36d4d9ab9b33c7
HEAD: 795d72da88c3557bc08995c0d23f90dc7792b05c

## Commits


## Stat
 README.md                            | 47 ++++--------------------------------
 frontend/app/components/RouteMap.vue |  1 -
 frontend/app/pages/index.vue         | 43 ---------------------------------
 3 files changed, 5 insertions(+), 86 deletions(-)

## Diff
diff --git a/README.md b/README.md
index 8d63b05..81bc99e 100644
--- a/README.md
+++ b/README.md
@@ -58,27 +58,28 @@ RainViewer tiles (corridor)
 - **Weather:** Open-Meteo (normalized ΓåÆ internal model ΓåÆ UI)
 
 ## Architecture
 
 ```text
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
 - Python 3.12+ (backend)
 
 ## Bß║»t ─æß║ºu nhanh
 
 ### 1. Cß║Ñu h├¼nh m├┤i tr╞░ß╗¥ng
@@ -182,65 +183,101 @@ Kh├┤ng commit credentials thß║¡t.
 ## API
 
 | Method | Path | M├┤ tß║ú |
 |---|---|---|
 | GET | `/api/health` | Health check |
 | GET | `/api/geocode` | Autocomplete ─æß╗ïa chß╗ë |
 | POST | `/api/route-weather` | Route + weather (single compute) |
 | GET | `/api/radar/current` | Metadata radar hiß╗çn tß║íi (tile URL, timestamp) |
 | GET | `/api/satellite/latest` | Metadata ß║únh vß╗ç tinh hiß╗çn tß║íi (tile URL, timestamp) |
 | POST | `/api/rain-cells/track` | Detect + track v├╣ng m╞░a trong h├ánh lang lß╗Ö tr├¼nh |
+| POST | `/api/nowcasting/predict` | Dß╗▒ b├ío vß╗ï tr├¡ v├╣ng m╞░a 5ΓÇô60 ph├║t (baseline extrapolation) |
 | POST | `/api/weather-fusion/state` | Unified multi-source weather state theo route segment |
 | POST | `/api/route-weather/compare` | So s├ính giß╗¥ xuß║Ñt ph├ít (backend; UI Stage 1 kh├┤ng d├╣ng) |
 
 ## Known limitations
 
 - Rain-cell detection d├╣ng tile RainViewer scheme 0 (grayscale proxy), ─æß╗Ö ph├ón giß║úi phß╗Ñ thuß╗Öc zoom/buffer
 - Baseline detector c├│ thß╗â nhß║ºm clutter/nhiß╗àu; kh├┤ng phß║úi storm-cell typing chuy├¬n m├┤n
 - Radar RainViewer: ─æß╗Ö ph├ón giß║úi ~1 km, cß║¡p nhß║¡t ~5ΓÇô10 ph├║t; tile chß╗ë c├│ ─æß║┐n **zoom 7** (map zoom s├óu h╞ín sß║╜ scale tile, kh├┤ng request z>7)
 - RainViewer free tier: attribution bß║»t buß╗Öc, kh├┤ng d├╣ng cho sß║ún phß║⌐m th╞░╞íng mß║íi trß║ú ph├¡ (xem [Terms](https://www.rainviewer.com/terms.html))
 - Open-Meteo ─æß╗Ö ph├ón giß║úi theo giß╗¥
 - GraphHopper free tier giß╗¢i hß║ín credit / non-commercial
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
 
 Implemented:
 - satellite integration (NASA GIBS Himawari WMTS) qua adapter/service ri├¬ng
 - satellite map layer ─æß╗Öc lß║¡p, bß║¡t/tß║»t ri├¬ng, chß╗ënh opacity
 - timestamp/freshness tracking cho radar, satellite, forecast, rain cells
 - source provenance preservation trong unified weather state
 - normalized weather state + deterministic fusion engine
 - data quality metadata (`GOOD`, `STALE`, `MISSING`, `CONFLICTING`, `UNKNOWN`)
 - route-oriented fused weather state (`/api/weather-fusion/state`)
 - corridor overlap: rain-cell g├ín v├áo segment gß║ºn nhß║Ñt nß║┐u nß║▒m trong `FUSION_CORRIDOR_KM` (kh├┤ng d├╣ng midpoint 50 km)
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
diff --git a/frontend/app/components/RouteMap.vue b/frontend/app/components/RouteMap.vue
index 7cf6c67..348eefa 100644
--- a/frontend/app/components/RouteMap.vue
+++ b/frontend/app/components/RouteMap.vue
@@ -684,20 +684,21 @@ onMounted(async () => {
   await ensureMap()
   if (map.value?.isStyleLoaded()) renderAll()
   else map.value?.once("load", renderAll)
 })
 
 onBeforeUnmount(() => {
   startMarker?.remove()
   endMarker?.remove()
   rainCellPopup?.remove()
   nowcastPopup?.remove()
+  nowcastClickBound = false
   map.value?.remove()
   map.value = null
 })
 </script>
 
 <style>
 /* Load after maplibre-gl.css ΓÇö rain-cell popup must not inherit app light text on white popup shell */
 .maplibregl-popup.rain-cell-popup .maplibregl-popup-content,
 .maplibregl-popup.nowcast-popup .maplibregl-popup-content {
   background: #1e293b !important;
diff --git a/frontend/app/pages/index.vue b/frontend/app/pages/index.vue
index d1bd37d..1d760af 100644
--- a/frontend/app/pages/index.vue
+++ b/frontend/app/pages/index.vue
@@ -36,31 +36,39 @@
         :loading="radarLoading"
         :error-message="radarError"
         :frame="radarFrame"
         :freshness-label="radarFreshness"
         :timestamp-display="radarTimestamp"
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
         :satellite-status="satelliteFrame?.status ?? null"
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
 
       <FusionDebugPanel
         :enabled="fusionDebugEnabled"
         :loading="fusionLoading"
         :error-message="fusionError"
         :state="fusionState"
@@ -81,32 +89,38 @@
             :radar-enabled="radarEnabled"
             :radar-opacity="radarOpacity"
             :radar-tile-url="radarTileUrl"
             :radar-tile-max-zoom="radarTileMaxZoom"
             :satellite-enabled="satelliteEnabled"
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
   errorMessage,
   weatherWarning,
   originQuery,
   destinationQuery,
   originSuggestions,
@@ -139,20 +153,32 @@ const {
   enabled: rainCellsEnabled,
   loading: rainCellsLoading,
   errorMessage: rainCellsError,
   cells: trackedCells,
   cellCount,
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
   frame: satelliteFrame,
   freshnessLabel: satelliteFreshness,
   timestampDisplay: satelliteTimestamp,
   fetchSatellite,
   setEnabled: setSatelliteEnabled,
@@ -168,38 +194,55 @@ const {
 } = useWeatherFusion()
 
 const routeGeometry = computed(() => {
   if (!routeWeather.value?.segments) return null
   return routeWeather.value.segments.flatMap((s) => s.coordinates ?? [])
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
 
 watch([routeGeometry, rainCellsEnabled], ([geom, enabled]) => {
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
   satelliteEnabled.value && satelliteFrame.value?.tile_url_template ? satelliteFrame.value.tile_url_template : null,
 )
 const satelliteTileMaxZoom = computed(() => satelliteFrame.value?.tile_max_zoom ?? 6)
 
 const departureDisplay = computed(() => (departureLocal.value ? departureLocal.value.slice(11, 16) : "ΓÇö"))

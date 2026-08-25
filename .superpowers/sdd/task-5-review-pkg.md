# Review package Task 5
BASE: 0f4bf317457579bd3415a4ec531f360fc5d37a97
HEAD: 270b8d9031e897fcf9bd1c57891458494cefcae0

## Commits


## Stat
 frontend/app/composables/useNowcasting.ts | 105 ------------------------------
 frontend/app/types/nowcasting.ts          |  45 -------------
 frontend/app/utils/nowcast.ts             |  64 ------------------
 3 files changed, 214 deletions(-)

## Diff
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
index 0000000..d35dd13
--- /dev/null
+++ b/frontend/app/utils/nowcast.ts
@@ -0,0 +1,64 @@
+import type { PredictedRainCell } from "~/types/nowcasting"
+import { bearingToCompass } from "~/utils/rainCell"
+
+export function intensityLabel(intensity: number | null): string {
+  if (intensity == null) return "Kh├┤ng r├╡"
+  if (intensity < 40) return "nhß║╣"
+  if (intensity < 90) return "vß╗½a"
+  return "mß║ính"
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
+        properties: {
+          cell_id: c.cell_id,
+          forecast_minutes: c.forecast_minutes,
+          kind: c.kind,
+        },
+      }
+    })
+
+  const pointFeatures = cells.map((c) => ({
+    type: "Feature" as const,
+    geometry: {
+      type: "Point" as const,
+      coordinates: [c.centroid.lng, c.centroid.lat],
+    },
+    properties: {
+      cell_id: c.cell_id,
+      forecast_minutes: c.forecast_minutes,
+      kind: c.kind,
+      rain_probability: c.rain_probability,
+      rain_intensity: c.rain_intensity,
+      intensity_label: intensityLabel(c.rain_intensity),
+      confidence: c.confidence,
+      speed_kmh: c.motion?.speed_kmh ?? null,
+      bearing: c.motion?.bearing_degrees ?? null,
+      bearing_compass:
+        c.motion?.bearing_degrees != null ? bearingToCompass(c.motion.bearing_degrees) : null,
+      source: c.source,
+    },
+  }))
+
+  return {
+    bbox: { type: "FeatureCollection" as const, features: bboxFeatures },
+    points: { type: "FeatureCollection" as const, features: pointFeatures },
+  }
+}

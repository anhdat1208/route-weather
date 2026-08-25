# Review package Task 7
BASE: 7c3d6468110b9287dac7f75a0e0bf13620b74b9d
HEAD: ea673cc72fe464aa378fa2bb3c36d4d9ab9b33c7

## Commits


## Stat
 frontend/app/components/RouteMap.vue | 172 +----------------------------------
 frontend/app/utils/nowcast.ts        | 101 ++++----------------
 2 files changed, 23 insertions(+), 250 deletions(-)

## Diff
diff --git a/frontend/app/components/RouteMap.vue b/frontend/app/components/RouteMap.vue
index b953434..7cf6c67 100644
--- a/frontend/app/components/RouteMap.vue
+++ b/frontend/app/components/RouteMap.vue
@@ -1,32 +1,38 @@
 <template>
   <div ref="mapEl" class="h-full w-full" />
 </template>
 
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
   radarTileUrl?: string | null
   radarTileMaxZoom?: number
   satelliteEnabled?: boolean
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
 let maplibreModule: typeof import("maplibre-gl") | null = null
 let startMarker: maplibregl.Marker | null = null
 let endMarker: maplibregl.Marker | null = null
 
 const ROUTE_SOURCE = "route-line"
@@ -37,22 +43,31 @@ const WEATHER_LAYER = "weather-points"
 const RADAR_SOURCE = "radar-tiles"
 const RADAR_LAYER = "radar-tiles"
 const SATELLITE_SOURCE = "satellite-tiles"
 const SATELLITE_LAYER = "satellite-tiles"
 const RAIN_CELLS_POINTS_SOURCE = "rain-cells-points"
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
   await new Promise((r) => requestAnimationFrame(() => r(null)))
   if (!mapEl.value) return
   map.value = new maplibreModule.Map({
     container: mapEl.value,
     style: config.public.mapStyleUrl,
@@ -373,20 +388,155 @@ function syncRainCellLayers() {
     })
     m.on("mouseenter", RAIN_CELLS_POINT_LAYER, () => {
       m.getCanvas().style.cursor = "pointer"
     })
     m.on("mouseleave", RAIN_CELLS_POINT_LAYER, () => {
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
 
   if (m.getLayer(ROUTE_GLOW_LAYER)) m.removeLayer(ROUTE_GLOW_LAYER)
   removeLayerSource(m, ROUTE_LAYER, ROUTE_SOURCE)
   removeLayerSource(m, WEATHER_LAYER, WEATHER_SOURCE)
 
   const lineCoords = data.segments.flatMap((s) => s.coordinates.map((p) => [p.lng, p.lat] as [number, number]))
@@ -462,20 +612,21 @@ function renderRouteLayers() {
     (b, c) => b.extend(c),
     new maplibreModule.LngLatBounds(lineCoords[0], lineCoords[0]),
   )
   m.fitBounds(bounds, { padding: 40 })
 }
 
 function renderAll() {
   syncSatelliteLayer()
   syncRadarLayer()
   syncRainCellLayers()
+  syncNowcastLayers()
   if (props.routeWeather) renderRouteLayers()
 }
 
 watch(
   () => [props.radarEnabled, props.radarOpacity, props.radarTileUrl, props.radarTileMaxZoom] as const,
   () => {
     if (!map.value) return
     if (map.value.isStyleLoaded()) {
       syncRadarLayer()
       if (props.routeWeather) renderRouteLayers()
@@ -501,52 +652,67 @@ watch(
 watch(
   () => [props.rainCellsEnabled, props.trackedCells] as const,
   () => {
     if (!map.value) return
     if (map.value.isStyleLoaded()) syncRainCellLayers()
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
     if (map.value.isStyleLoaded()) renderAll()
     else map.value.once("load", renderAll)
   },
   { deep: true },
 )
 
 onMounted(async () => {
   await ensureMap()
   if (map.value?.isStyleLoaded()) renderAll()
   else map.value?.once("load", renderAll)
 })
 
 onBeforeUnmount(() => {
   startMarker?.remove()
   endMarker?.remove()
+  rainCellPopup?.remove()
+  nowcastPopup?.remove()
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
diff --git a/frontend/app/utils/nowcast.ts b/frontend/app/utils/nowcast.ts
index d35dd13..90e754a 100644
--- a/frontend/app/utils/nowcast.ts
+++ b/frontend/app/utils/nowcast.ts
@@ -1,64 +1,125 @@
-import type { PredictedRainCell } from "~/types/nowcasting"
+import type { NowcastModelInfo, PredictedRainCell } from "~/types/nowcasting"
 import { bearingToCompass } from "~/utils/rainCell"
 
 export function intensityLabel(intensity: number | null): string {
   if (intensity == null) return "Kh├┤ng r├╡"
   if (intensity < 40) return "nhß║╣"
   if (intensity < 90) return "vß╗½a"
   return "mß║ính"
 }
 
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
 export function nowcastGeoJson(cells: PredictedRainCell[]) {
   const bboxFeatures = cells
     .filter((c) => c.bounds)
     .map((c) => {
       const b = c.bounds!
       return {
         type: "Feature" as const,
         geometry: {
           type: "Polygon" as const,
           coordinates: [
             [
               [b.west, b.north],
               [b.east, b.north],
               [b.east, b.south],
               [b.west, b.south],
               [b.west, b.north],
             ],
           ],
         },
-        properties: {
-          cell_id: c.cell_id,
-          forecast_minutes: c.forecast_minutes,
-          kind: c.kind,
-        },
+        properties: nowcastFeatureProperties(c),
       }
     })
 
   const pointFeatures = cells.map((c) => ({
     type: "Feature" as const,
     geometry: {
       type: "Point" as const,
       coordinates: [c.centroid.lng, c.centroid.lat],
     },
-    properties: {
-      cell_id: c.cell_id,
-      forecast_minutes: c.forecast_minutes,
-      kind: c.kind,
-      rain_probability: c.rain_probability,
-      rain_intensity: c.rain_intensity,
-      intensity_label: intensityLabel(c.rain_intensity),
-      confidence: c.confidence,
-      speed_kmh: c.motion?.speed_kmh ?? null,
-      bearing: c.motion?.bearing_degrees ?? null,
-      bearing_compass:
-        c.motion?.bearing_degrees != null ? bearingToCompass(c.motion.bearing_degrees) : null,
-      source: c.source,
-    },
+    properties: nowcastFeatureProperties(c),
   }))
 
   return {
     bbox: { type: "FeatureCollection" as const, features: bboxFeatures },
     points: { type: "FeatureCollection" as const, features: pointFeatures },
   }
 }

<template>
  <div ref="mapEl" class="h-full w-full" />
</template>

<script setup lang="ts">
import type maplibregl from "maplibre-gl"
import type { RouteWeatherResponse } from "~/types/routeWeather"
import type { TrackedRainCell } from "~/types/rainCell"
import { bearingToCompass } from "~/utils/rainCell"

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
}>()

const config = useRuntimeConfig()
const mapEl = ref<HTMLElement | null>(null)
const map = shallowRef<maplibregl.Map | null>(null)
let maplibreModule: typeof import("maplibre-gl") | null = null
let startMarker: maplibregl.Marker | null = null
let endMarker: maplibregl.Marker | null = null

const ROUTE_SOURCE = "route-line"
const ROUTE_GLOW_LAYER = "route-line-glow"
const ROUTE_LAYER = "route-line"
const WEATHER_SOURCE = "weather-points"
const WEATHER_LAYER = "weather-points"
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

let rainCellPopup: maplibregl.Popup | null = null

async function ensureMap() {
  if (!process.client || map.value || !mapEl.value) return
  maplibreModule = await import("maplibre-gl")
  await import("maplibre-gl/dist/maplibre-gl.css")
  await new Promise((r) => requestAnimationFrame(() => r(null)))
  if (!mapEl.value) return
  map.value = new maplibreModule.Map({
    container: mapEl.value,
    style: config.public.mapStyleUrl,
    center: [106.67, 10.78],
    zoom: 11,
  })
  try {
    map.value.addControl(new maplibreModule.NavigationControl(), "right")
  } catch {
    // Container may be detached during SSR/hydration races.
  }
}

function removeLayerSource(m: maplibregl.Map, layerId: string, sourceId: string) {
  if (m.getLayer(layerId)) m.removeLayer(layerId)
  if (m.getSource(sourceId)) m.removeSource(sourceId)
}

function firstSymbolLayerId(m: maplibregl.Map): string | undefined {
  const layers = m.getStyle()?.layers
  if (!layers) return undefined
  const symbol = layers.find((l) => l.type === "symbol")
  return symbol?.id
}

function weatherPointCoords(data: RouteWeatherResponse): [number, number][] {
  const coords: [number, number][] = []
  const segs = data.segments
  for (let i = 0; i < data.timeline.length; i++) {
    if (i < segs.length && segs[i].coordinates.length) {
      const p = segs[i].coordinates[0]
      coords.push([p.lng, p.lat])
    } else if (segs.length) {
      const last = segs[segs.length - 1]
      const p = last.coordinates[last.coordinates.length - 1]
      if (p) coords.push([p.lng, p.lat])
    }
  }
  return coords
}

function syncRadarLayer() {
  if (!map.value || !maplibreModule) return
  const m = map.value
  const showRadar = props.radarEnabled && props.radarTileUrl

  if (!showRadar) {
    removeLayerSource(m, RADAR_LAYER, RADAR_SOURCE)
    if (m.getLayer(ROUTE_GLOW_LAYER)) m.removeLayer(ROUTE_GLOW_LAYER)
    return
  }

  const opacity = props.radarOpacity ?? 0.65
  const tileMaxZoom = props.radarTileMaxZoom ?? 7
  const beforeId = m.getLayer(ROUTE_LAYER) ? ROUTE_LAYER : firstSymbolLayerId(m)

  const existing = m.getSource(RADAR_SOURCE) as maplibregl.RasterTileSource | undefined
  if (existing && "setTiles" in existing) {
    existing.setTiles([props.radarTileUrl!])
    m.setPaintProperty(RADAR_LAYER, "raster-opacity", opacity)
    return
  }

  removeLayerSource(m, RADAR_LAYER, RADAR_SOURCE)

  // RainViewer only serves tiles up to z=7; overzoom at higher map zoom levels.
  m.addSource(RADAR_SOURCE, {
    type: "raster",
    tiles: [props.radarTileUrl!],
    tileSize: 256,
    maxzoom: tileMaxZoom,
    attribution: "© RainViewer",
  })

  m.addLayer(
    {
      id: RADAR_LAYER,
      type: "raster",
      source: RADAR_SOURCE,
      paint: {
        "raster-opacity": opacity,
        "raster-fade-duration": 300,
      },
    },
    beforeId,
  )
}

function syncSatelliteLayer() {
  if (!map.value || !maplibreModule) return
  const m = map.value
  const showSatellite = props.satelliteEnabled && props.satelliteTileUrl

  if (!showSatellite) {
    removeLayerSource(m, SATELLITE_LAYER, SATELLITE_SOURCE)
    return
  }

  const opacity = props.satelliteOpacity ?? 0.45
  const tileMaxZoom = props.satelliteTileMaxZoom ?? 6
  const beforeId = m.getLayer(ROUTE_LAYER) ? ROUTE_LAYER : firstSymbolLayerId(m)
  const existing = m.getSource(SATELLITE_SOURCE) as maplibregl.RasterTileSource | undefined
  if (existing && "setTiles" in existing) {
    existing.setTiles([props.satelliteTileUrl!])
    m.setPaintProperty(SATELLITE_LAYER, "raster-opacity", opacity)
    return
  }

  removeLayerSource(m, SATELLITE_LAYER, SATELLITE_SOURCE)
  m.addSource(SATELLITE_SOURCE, {
    type: "raster",
    tiles: [props.satelliteTileUrl!],
    tileSize: 256,
    maxzoom: tileMaxZoom,
    attribution: "© NASA GIBS / JMA Himawari",
  })
  m.addLayer(
    {
      id: SATELLITE_LAYER,
      type: "raster",
      source: SATELLITE_SOURCE,
      paint: {
        "raster-opacity": opacity,
        "raster-fade-duration": 300,
      },
    },
    beforeId,
  )
}

function rainCellGeoJson(cells: TrackedRainCell[]) {
  const bboxFeatures = cells
    .filter((c) => c.current.bounds)
    .map((c) => {
      const b = c.current.bounds!
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
        properties: {
          id: c.id,
          state: c.state,
        },
      }
    })

  const pointFeatures = cells.map((c) => ({
    type: "Feature" as const,
    geometry: {
      type: "Point" as const,
      coordinates: [c.current.centroid.lng, c.current.centroid.lat],
    },
    properties: {
      id: c.id,
      state: c.state,
      area_km2: c.current.area_km2 ?? null,
      intensity_mean: c.current.intensity?.mean ?? null,
      speed_kmh: c.motion?.speed_kmh ?? null,
      bearing: c.motion?.bearing_degrees ?? null,
      updated: c.current.timestamp,
      distance_km: c.distance_to_route_km ?? null,
    },
  }))

  const motionFeatures = cells
    .filter((c) => c.motion?.from_point && c.motion?.to_point)
    .map((c) => ({
      type: "Feature" as const,
      geometry: {
        type: "LineString" as const,
        coordinates: [
          [c.motion!.from_point!.lng, c.motion!.from_point!.lat],
          [c.motion!.to_point!.lng, c.motion!.to_point!.lat],
        ],
      },
      properties: { id: c.id },
    }))

  return {
    bbox: { type: "FeatureCollection" as const, features: bboxFeatures },
    points: { type: "FeatureCollection" as const, features: pointFeatures },
    motion: { type: "FeatureCollection" as const, features: motionFeatures },
  }
}

function formatRainCellPopup(props: Record<string, unknown>): string {
  const lineStyle = 'style="color:#e2e8f0;margin:0 0 4px 0"'
  const lines: string[] = [`<p ${lineStyle}><strong style="color:#f8fafc">Vùng mưa</strong></p>`]
  if (props.intensity_mean != null) {
    lines.push(`<p ${lineStyle}>Chỉ số cường độ: ${Number(props.intensity_mean).toFixed(0)}</p>`)
  }
  if (props.area_km2 != null) {
    lines.push(`<p ${lineStyle}>Diện tích: ~${Number(props.area_km2).toFixed(1)} km²</p>`)
  }
  if (props.speed_kmh != null && props.bearing != null) {
    lines.push(
      `<p ${lineStyle}>Di chuyển: ${bearingToCompass(Number(props.bearing))} · ${Number(props.speed_kmh).toFixed(0)} km/h</p>`,
    )
  }
  if (props.distance_km != null) {
    lines.push(`<p ${lineStyle}>Khoảng cách tới lộ trình: ${Number(props.distance_km).toFixed(1)} km</p>`)
  }
  if (props.updated) {
    const t = new Date(String(props.updated))
    lines.push(
      `<p ${lineStyle}>Cập nhật: ${t.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Bangkok" })}</p>`,
    )
  }
  lines.push('<p style="color:#94a3b8;font-size:11px;margin:6px 0 0 0">Quan sát hiện tại — không phải dự báo</p>')
  return `<div style="color:#e2e8f0;font-size:13px;line-height:1.45">${lines.join("")}</div>`
}

function styleRainCellPopupElement(popup: maplibregl.Popup) {
  const root = popup.getElement()
  if (!root) return
  const content = root.querySelector(".maplibregl-popup-content") as HTMLElement | null
  const tip = root.querySelector(".maplibregl-popup-tip") as HTMLElement | null
  if (content) {
    content.style.background = "#1e293b"
    content.style.color = "#e2e8f0"
    content.style.borderRadius = "8px"
    content.style.boxShadow = "0 8px 24px rgba(15, 23, 42, 0.45)"
    content.style.padding = "10px 12px"
  }
  if (tip) tip.style.borderTopColor = "#1e293b"
  const close = root.querySelector(".maplibregl-popup-close-button") as HTMLElement | null
  if (close) close.style.color = "#94a3b8"
}

function syncRainCellLayers() {
  if (!map.value || !maplibreModule) return
  const m = map.value
  const show = props.rainCellsEnabled && (props.trackedCells?.length ?? 0) > 0

  if (!show) {
    removeLayerSource(m, RAIN_CELLS_MOTION_LAYER, RAIN_CELLS_MOTION_SOURCE)
    removeLayerSource(m, RAIN_CELLS_POINT_LAYER, RAIN_CELLS_POINTS_SOURCE)
    removeLayerSource(m, RAIN_CELLS_BBOX_LAYER, RAIN_CELLS_BBOX_SOURCE)
    rainCellPopup?.remove()
    return
  }

  const gj = rainCellGeoJson(props.trackedCells!)
  const beforeRoute = m.getLayer(ROUTE_LAYER) ? ROUTE_LAYER : firstSymbolLayerId(m)

  const upsert = (sourceId: string, layerId: string, data: GeoJSON.FeatureCollection, layerSpec: maplibregl.LayerSpecification) => {
    if (m.getSource(sourceId)) {
      ;(m.getSource(sourceId) as maplibregl.GeoJSONSource).setData(data)
    } else {
      m.addSource(sourceId, { type: "geojson", data })
      m.addLayer(layerSpec, beforeRoute ?? undefined)
    }
  }

  upsert(RAIN_CELLS_BBOX_SOURCE, RAIN_CELLS_BBOX_LAYER, gj.bbox, {
    id: RAIN_CELLS_BBOX_LAYER,
    type: "line",
    source: RAIN_CELLS_BBOX_SOURCE,
    paint: {
      "line-color": "#f97316",
      "line-width": 2,
      "line-opacity": 0.55,
      "line-dasharray": [2, 2],
    },
  })

  upsert(RAIN_CELLS_MOTION_SOURCE, RAIN_CELLS_MOTION_LAYER, gj.motion, {
    id: RAIN_CELLS_MOTION_LAYER,
    type: "line",
    source: RAIN_CELLS_MOTION_SOURCE,
    paint: {
      "line-color": "#fb923c",
      "line-width": 3,
      "line-opacity": 0.9,
    },
  })

  if (m.getSource(RAIN_CELLS_POINTS_SOURCE)) {
    ;(m.getSource(RAIN_CELLS_POINTS_SOURCE) as maplibregl.GeoJSONSource).setData(gj.points)
  } else {
    m.addSource(RAIN_CELLS_POINTS_SOURCE, { type: "geojson", data: gj.points })
    m.addLayer(
      {
        id: RAIN_CELLS_POINT_LAYER,
        type: "circle",
        source: RAIN_CELLS_POINTS_SOURCE,
        paint: {
          "circle-radius": 7,
          "circle-color": ["match", ["get", "state"], "LOST", "#94a3b8", "NEW", "#fbbf24", "#ef4444"],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#0f172a",
        },
      },
      beforeRoute ?? undefined,
    )
    m.on("click", RAIN_CELLS_POINT_LAYER, (e) => {
      const f = e.features?.[0]
      if (!f?.properties || !e.lngLat) return
      if (!rainCellPopup) {
        rainCellPopup = new maplibreModule!.Popup({
          closeButton: true,
          maxWidth: "280px",
          className: "rain-cell-popup",
        })
      }
      rainCellPopup.setLngLat(e.lngLat).setHTML(formatRainCellPopup(f.properties as Record<string, unknown>)).addTo(m)
      styleRainCellPopupElement(rainCellPopup)
    })
    m.on("mouseenter", RAIN_CELLS_POINT_LAYER, () => {
      m.getCanvas().style.cursor = "pointer"
    })
    m.on("mouseleave", RAIN_CELLS_POINT_LAYER, () => {
      m.getCanvas().style.cursor = ""
    })
  }
}

function renderRouteLayers() {
  if (!map.value || !maplibreModule || !props.routeWeather) return
  const m = map.value
  const data = props.routeWeather

  if (m.getLayer(ROUTE_GLOW_LAYER)) m.removeLayer(ROUTE_GLOW_LAYER)
  removeLayerSource(m, ROUTE_LAYER, ROUTE_SOURCE)
  removeLayerSource(m, WEATHER_LAYER, WEATHER_SOURCE)

  const lineCoords = data.segments.flatMap((s) => s.coordinates.map((p) => [p.lng, p.lat] as [number, number]))
  if (!lineCoords.length) return

  m.addSource(ROUTE_SOURCE, {
    type: "geojson",
    data: {
      type: "Feature",
      geometry: { type: "LineString", coordinates: lineCoords },
      properties: {},
    },
  })

  // Glow under route when radar is visible for contrast.
  if (props.radarEnabled && props.radarTileUrl) {
    m.addLayer({
      id: ROUTE_GLOW_LAYER,
      source: ROUTE_SOURCE,
      type: "line",
      paint: {
        "line-color": "#ffffff",
        "line-width": 9,
        "line-opacity": 0.55,
        "line-blur": 1,
      },
    })
  }

  m.addLayer({
    id: ROUTE_LAYER,
    source: ROUTE_SOURCE,
    type: "line",
    paint: {
      "line-color": "#38bdf8",
      "line-width": 5,
      "line-opacity": 0.95,
    },
  })

  const pointCoords = weatherPointCoords(data)
  m.addSource(WEATHER_SOURCE, {
    type: "geojson",
    data: {
      type: "FeatureCollection",
      features: pointCoords.map((c, i) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: c },
        properties: { index: i },
      })),
    },
  })
  m.addLayer({
    id: WEATHER_LAYER,
    source: WEATHER_SOURCE,
    type: "circle",
    paint: {
      "circle-radius": 6,
      "circle-color": "#fbbf24",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#0f172a",
    },
  })

  if (startMarker) startMarker.remove()
  if (endMarker) endMarker.remove()
  const first = lineCoords[0]
  const last = lineCoords[lineCoords.length - 1]
  startMarker = new maplibreModule.Marker({ color: "#22c55e" }).setLngLat(first).addTo(m)
  endMarker = new maplibreModule.Marker({ color: "#ef4444" }).setLngLat(last).addTo(m)

  const bounds = lineCoords.reduce(
    (b, c) => b.extend(c),
    new maplibreModule.LngLatBounds(lineCoords[0], lineCoords[0]),
  )
  m.fitBounds(bounds, { padding: 40 })
}

function renderAll() {
  syncSatelliteLayer()
  syncRadarLayer()
  syncRainCellLayers()
  if (props.routeWeather) renderRouteLayers()
}

watch(
  () => [props.radarEnabled, props.radarOpacity, props.radarTileUrl, props.radarTileMaxZoom] as const,
  () => {
    if (!map.value) return
    if (map.value.isStyleLoaded()) {
      syncRadarLayer()
      if (props.routeWeather) renderRouteLayers()
    } else {
      map.value.once("load", renderAll)
    }
  },
)

watch(
  () => [props.satelliteEnabled, props.satelliteOpacity, props.satelliteTileUrl, props.satelliteTileMaxZoom] as const,
  () => {
    if (!map.value) return
    if (map.value.isStyleLoaded()) {
      syncSatelliteLayer()
      if (props.routeWeather) renderRouteLayers()
    } else {
      map.value.once("load", renderAll)
    }
  },
)

watch(
  () => [props.rainCellsEnabled, props.trackedCells] as const,
  () => {
    if (!map.value) return
    if (map.value.isStyleLoaded()) syncRainCellLayers()
    else map.value.once("load", renderAll)
  },
  { deep: true },
)

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
  map.value?.remove()
  map.value = null
})
</script>

<style>
/* Load after maplibre-gl.css — rain-cell popup must not inherit app light text on white popup shell */
.maplibregl-popup.rain-cell-popup .maplibregl-popup-content {
  background: #1e293b !important;
  color: #e2e8f0 !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.45) !important;
}

.maplibregl-popup.rain-cell-popup .maplibregl-popup-tip {
  border-top-color: #1e293b !important;
}

.maplibregl-popup.rain-cell-popup .maplibregl-popup-close-button {
  color: #94a3b8 !important;
}
</style>

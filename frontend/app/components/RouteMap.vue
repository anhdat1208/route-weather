<template>
  <div ref="mapEl" class="h-full w-full" />
</template>

<script setup lang="ts">
import type maplibregl from "maplibre-gl"
import type { RouteWeatherResponse } from "~/types/routeWeather"

const props = defineProps<{
  routeWeather: RouteWeatherResponse | null
  radarEnabled?: boolean
  radarOpacity?: number
  radarTileUrl?: string | null
  radarTileMaxZoom?: number
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
  syncRadarLayer()
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

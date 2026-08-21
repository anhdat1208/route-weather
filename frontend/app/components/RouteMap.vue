<template>
  <div ref="mapEl" class="h-full w-full" />
</template>

<script setup lang="ts">
import type maplibregl from "maplibre-gl"
import type { RouteWeatherResponse } from "~/types/routeWeather"

// Future map layers (Stage 2+): radar, satellite, rain-cell, traffic.
// Keep adding as separate sources/layers beside route-line and weather-points.

const props = defineProps<{ routeWeather: RouteWeatherResponse | null }>()

const config = useRuntimeConfig()
const mapEl = ref<HTMLElement | null>(null)
const map = shallowRef<maplibregl.Map | null>(null)
let maplibreModule: typeof import("maplibre-gl") | null = null
let startMarker: maplibregl.Marker | null = null
let endMarker: maplibregl.Marker | null = null

const ROUTE_SOURCE = "route-line"
const ROUTE_LAYER = "route-line"
const WEATHER_SOURCE = "weather-points"
const WEATHER_LAYER = "weather-points"

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

function renderLayers() {
  if (!map.value || !maplibreModule || !props.routeWeather) return
  const m = map.value
  const data = props.routeWeather

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
  m.addLayer({
    id: ROUTE_LAYER,
    source: ROUTE_SOURCE,
    type: "line",
    paint: {
      "line-color": "#38bdf8",
      "line-width": 5,
      "line-opacity": 0.9,
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
      "circle-stroke-width": 1,
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

watch(
  () => props.routeWeather,
  async () => {
    await ensureMap()
    if (!props.routeWeather || !map.value) return
    if (map.value.isStyleLoaded()) renderLayers()
    else map.value.once("load", renderLayers)
  },
  { deep: true },
)

onMounted(async () => {
  await ensureMap()
  if (props.routeWeather) {
    if (map.value?.isStyleLoaded()) renderLayers()
    else map.value?.once("load", renderLayers)
  }
})

onBeforeUnmount(() => {
  startMarker?.remove()
  endMarker?.remove()
  map.value?.remove()
  map.value = null
})
</script>

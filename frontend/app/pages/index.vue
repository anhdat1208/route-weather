<template>
  <div class="flex h-screen overflow-hidden flex-col md:flex-row">
    <aside class="flex w-full shrink-0 flex-col gap-4 overflow-y-auto border-r border-slate-700/50 p-4 md:w-80">
      <div class="mb-2">
        <h1 class="text-xl font-bold">Route Weather</h1>
        <p class="mt-1 text-xs text-slate-400">Biết thời tiết trên từng chặng đường</p>
      </div>

      <div class="card space-y-3">
        <div class="relative">
          <label class="mb-1 block text-xs text-slate-400">Điểm đi</label>
          <input v-model="originQuery" class="input-field" type="text" placeholder="Nhập địa chỉ xuất phát..." />
          <div v-if="originSuggestions.length" class="absolute z-20 mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 shadow-lg">
            <button
              v-for="item in originSuggestions"
              :key="`o-${item.label}-${item.point.lat}`"
              class="block w-full px-3 py-2 text-left text-xs text-slate-100 hover:bg-slate-800"
              @click="selectOrigin(item)"
            >
              {{ item.label }}
              <span v-if="item.approximate" class="ml-1 text-[10px] text-amber-300">(gần đúng theo tên đường)</span>
            </button>
          </div>
        </div>

        <div class="relative">
          <label class="mb-1 block text-xs text-slate-400">Điểm đến</label>
          <input v-model="destinationQuery" class="input-field" type="text" placeholder="Nhập địa chỉ đích..." />
          <div v-if="destinationSuggestions.length" class="absolute z-20 mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 shadow-lg">
            <button
              v-for="item in destinationSuggestions"
              :key="`d-${item.label}-${item.point.lat}`"
              class="block w-full px-3 py-2 text-left text-xs text-slate-100 hover:bg-slate-800"
              @click="selectDestination(item)"
            >
              {{ item.label }}
              <span v-if="item.approximate" class="ml-1 text-[10px] text-amber-300">(gần đúng theo tên đường)</span>
            </button>
          </div>
        </div>

        <div>
          <label class="mb-1 block text-xs text-slate-400">Phương tiện</label>
          <select v-model="travelMode" class="input-field">
            <option value="motorbike">Xe máy</option>
            <option value="walking">Đi bộ</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs text-slate-400">Thời gian xuất phát</label>
          <input v-model="departureLocal" class="input-field" type="datetime-local" />
        </div>
        <button class="btn-primary" :disabled="loading || !originSelected || !destinationSelected" @click="runRouteWeather">
          {{ loading ? "Đang tính..." : "Tìm lộ trình & thời tiết" }}
        </button>
        <p v-if="errorMessage" class="text-xs text-red-400">{{ errorMessage }}</p>
      </div>

      <div class="card space-y-2">
        <h2 class="text-sm font-semibold text-slate-300">Tổng quan hành trình</h2>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div><span class="text-slate-400">Khoảng cách</span><p class="font-medium">{{ routeWeather?.route.distance_km?.toFixed(1) ?? "—" }} km</p></div>
          <div><span class="text-slate-400">Thời gian di chuyển</span><p class="font-medium">{{ routeWeather ? Math.round(routeWeather.route.duration_minutes) : "—" }} phút</p></div>
          <div><span class="text-slate-400">Xuất phát</span><p class="font-medium">{{ departureDisplay }}</p></div>
          <div><span class="text-slate-400">Đến nơi dự kiến</span><p class="font-medium">{{ etaDisplay }}</p></div>
        </div>
      </div>

      <div class="card">
        <h2 class="mb-2 text-sm font-semibold text-slate-300">Weather Risk Score</h2>
        <div class="flex items-center gap-3">
          <div v-if="routeWeather" class="relative h-16 w-16">
            <svg class="h-16 w-16" viewBox="0 0 36 36">
              <circle cx="18" cy="18" r="15.915" fill="none" stroke="#334155" stroke-width="3" />
              <circle
                cx="18"
                cy="18"
                r="15.915"
                fill="none"
                :stroke="riskColor(routeWeather.risk.level)"
                stroke-width="3"
                stroke-linecap="round"
                :stroke-dasharray="`${gaugeCircumference} ${gaugeCircumference}`"
                :stroke-dashoffset="gaugeDashOffset"
              />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
              <span class="text-sm font-semibold">{{ Math.round(routeWeather.risk.score) }}</span>
            </div>
          </div>
          <div v-else class="flex h-16 w-16 items-center justify-center rounded-full border-4 border-slate-600">
            <span class="text-lg font-semibold text-slate-400">—</span>
          </div>
          <div>
            <p class="text-sm font-medium">{{ routeWeather ? riskLabel(routeWeather.risk.level) : "Chưa có dữ liệu" }}</p>
            <p class="text-xs text-slate-400">{{ worstSegmentCaption ?? routeWeather?.risk.summary ?? "Nhập lộ trình để xem rủi ro." }}</p>
          </div>
        </div>
      </div>

      <div class="card" v-if="routeWeather?.recommendation?.message">
        <h2 class="mb-1 text-sm font-semibold text-slate-300">Gợi ý</h2>
        <p class="text-xs text-slate-300">{{ routeWeather.recommendation.message }}</p>
      </div>
    </aside>

    <main class="flex flex-1 flex-col overflow-hidden">
      <div class="flex items-center justify-between border-b border-slate-700/50 px-4 py-2">
        <div class="flex gap-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="rounded-lg px-4 py-1.5 text-sm"
            :class="activeTab === tab.id ? 'bg-slate-700 font-medium text-white' : 'text-slate-400 hover:bg-slate-800'"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>
        <span class="rounded-full px-2 py-0.5 text-xs" :class="healthOk ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'">
          API {{ healthOk ? "online" : "offline" }}
        </span>
      </div>

      <div v-show="activeTab === 'map'" class="flex flex-1 flex-col">
        <div class="relative flex-1">
          <div ref="mapEl" class="h-full w-full" />

          <!-- Legend -->
          <div class="absolute right-4 top-4 w-44 rounded-xl border border-slate-700/50 bg-slate-900/70 p-3 text-xs backdrop-blur">
            <div class="mb-2 font-semibold text-slate-200">Chú thích</div>
            <div class="space-y-1">
              <div class="flex items-center gap-2"><span class="inline-block h-3 w-3 rounded-full" style="background:#22c55e"></span><span>Thấp</span></div>
              <div class="flex items-center gap-2"><span class="inline-block h-3 w-3 rounded-full" style="background:#f59e0b"></span><span>Trung bình</span></div>
              <div class="flex items-center gap-2"><span class="inline-block h-3 w-3 rounded-full" style="background:#f97316"></span><span>Cao</span></div>
              <div class="flex items-center gap-2"><span class="inline-block h-3 w-3 rounded-full" style="background:#ef4444"></span><span>Rất cao</span></div>
            </div>
          </div>
        </div>

        <!-- Timeline under map (mockup-like) -->
        <div class="border-t border-slate-700/50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-slate-200">Thời tiết trên lộ trình</h2>
            <span v-if="worstSegmentCaption" class="text-xs text-orange-300">
              {{ worstSegmentCaption }}
            </span>
          </div>

          <div v-if="routeWeather?.timeline?.length" class="space-y-3">
            <div class="flex items-stretch gap-2 overflow-x-auto pb-2">
              <div
                v-for="point in routeWeather.timeline"
                :key="`tp-${point.index}`"
                class="min-w-[140px] rounded-xl border px-3 py-2"
                :class="(point.index === worstPointIndex - 1 || point.index === worstPointIndex) ? 'border-red-400 bg-red-950/30' : 'border-slate-700/50 bg-slate-900/40'"
              >
                <div class="text-xs text-slate-400">{{ formatTime(point.arrival_time) }}</div>
                <div class="mt-1 text-sm font-medium">{{ point.label }}</div>
                <div class="mt-2 flex items-center justify-between">
                  <span class="text-lg">{{ weatherIcon(point) }}</span>
                  <span class="text-xs font-medium text-slate-200">{{ point.precipitation_probability_pct ?? 0 }}%</span>
                </div>
                <div class="mt-2 text-xs text-slate-400">{{ point.weather.temperature_c ?? "—" }}°C</div>
              </div>
            </div>

            <!-- Risk color bar -->
            <div class="relative h-2 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                v-for="(s, i) in riskBarSegments"
                :key="`bar-${i}`"
                class="absolute top-0 bottom-0"
                :style="{ left: `${s.leftPct}%`, width: `${s.widthPct}%`, background: s.color }"
              />
            </div>
            <div class="flex justify-between text-[11px] text-slate-500">
              <span>{{ routeWeather.timeline[0]?.distance_km.toFixed(1) }} km</span>
              <span>{{ routeWeather.timeline[routeWeather.timeline.length - 1]?.distance_km.toFixed(1) }} km</span>
            </div>
          </div>
          <div v-else class="text-sm text-slate-500">Chưa có timeline.</div>
        </div>
      </div>

      <div v-show="activeTab === 'timeline'" class="overflow-auto p-4">
        <h2 class="mb-3 text-sm font-semibold text-slate-300">Thời tiết trên lộ trình</h2>
        <div v-if="routeWeather?.timeline?.length" class="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div
            v-for="point in routeWeather.timeline"
            :key="`t-${point.index}`"
            class="rounded-xl border p-3"
            :class="(point.index === routeWeather.risk.worst_segment_index || point.index === routeWeather.risk.worst_segment_index + 1) ? 'border-red-400 bg-red-950/30' : 'border-slate-700 bg-slate-900/50'"
          >
            <p class="text-xs text-slate-400">{{ formatTime(point.arrival_time) }} · {{ point.label }}</p>
            <p class="mt-1 text-sm font-medium">{{ point.weather.condition ?? "Không rõ" }}</p>
            <p class="text-xs text-slate-300">{{ point.precipitation_probability_pct ?? 0 }}% · {{ point.precipitation_label?.label ?? "LOW" }}</p>
            <p class="text-xs text-slate-400">{{ point.weather.temperature_c ?? "—" }}°C</p>
          </div>
        </div>
        <p v-else class="text-sm text-slate-500">Chưa có timeline.</p>
      </div>

      <div v-show="activeTab === 'compare'" class="overflow-auto p-4">
        <h2 class="mb-3 text-sm font-semibold text-slate-300">So sánh thời gian xuất phát</h2>
        <div v-if="routeWeather?.recommendation?.alternatives?.length" class="space-y-2">
          <div
            v-for="alt in routeWeather.recommendation.alternatives"
            :key="alt.departure_time"
            class="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-900/50 p-3 text-sm"
          >
            <span>{{ formatTime(alt.departure_time) }}</span>
            <span class="font-semibold">{{ Math.round(alt.risk_score) }}</span>
            <span class="text-xs text-slate-400">{{ riskLabel(alt.level) }}</span>
          </div>
        </div>
        <p v-else class="text-sm text-slate-500">Chưa có dữ liệu so sánh.</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core"
import type maplibregl from "maplibre-gl"

type LatLng = { lat: number; lng: number }
type GeocodeResult = { label: string; point: LatLng; approximate?: boolean }
type RiskLevel = "very_low" | "low" | "moderate" | "high" | "very_high"

type RouteWeatherResponse = {
  route: { distance_km: number; duration_minutes: number }
  risk: { score: number; level: RiskLevel; summary: string; worst_segment_index: number | null }
  segments: Array<{
    index: number
    coordinates: LatLng[]
    start_distance_km: number
    end_distance_km: number
    risk_level: RiskLevel
    risk_score: number
  }>
  timeline: Array<{
    index: number
    label: string
    arrival_time: string
    distance_km: number
    weather: { condition: string | null; temperature_c: number | null }
    precipitation_probability_pct: number | null
    precipitation_label: { label: string } | null
  }>
  recommendation: {
    message: string
    alternatives: Array<{ departure_time: string; risk_score: number; level: RiskLevel }>
  }
}

const config = useRuntimeConfig()
const healthOk = ref(false)
const loading = ref(false)
const errorMessage = ref("")

const originQuery = ref("")
const destinationQuery = ref("")
const originSuggestions = ref<GeocodeResult[]>([])
const destinationSuggestions = ref<GeocodeResult[]>([])
const originSelected = ref<GeocodeResult | null>(null)
const destinationSelected = ref<GeocodeResult | null>(null)

const travelMode = ref<"motorbike" | "walking">("motorbike")

function toLocalDateTimeInputValue(date: Date) {
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const departureLocal = ref(toLocalDateTimeInputValue(new Date(Date.now() + 15 * 60 * 1000)))

const routeWeather = ref<RouteWeatherResponse | null>(null)
const activeTab = ref<"map" | "timeline" | "compare">("map")
const tabs = [
  { id: "map", label: "Bản đồ" },
  { id: "timeline", label: "Timeline" },
  { id: "compare", label: "So sánh thời gian" },
] as const

const gaugeRadius = 15.915
const gaugeCircumference = 2 * Math.PI * gaugeRadius
const gaugeDashOffset = computed(() => {
  if (!routeWeather.value) return gaugeCircumference
  const score = Math.max(0, Math.min(100, routeWeather.value.risk.score))
  const pct = score / 100
  return gaugeCircumference * (1 - pct)
})

const worstPointIndex = computed(() => {
  const idx = routeWeather.value?.risk.worst_segment_index
  return idx === null || idx === undefined ? -1 : idx + 1
})

const worstSegmentCaption = computed(() => {
  const data = routeWeather.value
  const idx = data?.risk.worst_segment_index
  if (idx === null || idx === undefined || !data?.timeline?.length) return null
  const start = data.timeline[idx]?.label
  const end = data.timeline[idx + 1]?.label
  if (!start || !end) return data.risk.summary || `Đoạn nguy cơ cao nhất: Đoạn ${idx + 1}`
  return `Đoạn nguy cơ cao nhất: ${start} → ${end}`
})

const riskBarSegments = computed(() => {
  if (!routeWeather.value) return []
  const total = routeWeather.value.route.distance_km
  if (!total || total <= 0) return []

  return routeWeather.value.segments.map((s) => {
    const leftPct = (s.start_distance_km / total) * 100
    const widthPct = ((s.end_distance_km - s.start_distance_km) / total) * 100
    return { leftPct, widthPct: Math.max(0, widthPct), color: riskColor(s.risk_level) }
  })
})

const departureDisplay = computed(() => departureLocal.value ? departureLocal.value.slice(11, 16) : "—")
const etaDisplay = computed(() => {
  if (!routeWeather.value) return "—"
  const dep = new Date(departureLocal.value)
  dep.setMinutes(dep.getMinutes() + Math.round(routeWeather.value.route.duration_minutes))
  return dep.toTimeString().slice(0, 5)
})

const mapEl = ref<HTMLElement | null>(null)
const map = shallowRef<maplibregl.Map | null>(null)
let maplibreModule: typeof import("maplibre-gl") | null = null
let startMarker: maplibregl.Marker | null = null
let endMarker: maplibregl.Marker | null = null

function formatTime(v: string) {
  const d = new Date(v)
  return d.toTimeString().slice(0, 5)
}

function riskColor(level: RiskLevel) {
  if (level === "very_low") return "#22c55e"
  if (level === "low") return "#84cc16"
  if (level === "moderate") return "#f59e0b"
  if (level === "high") return "#f97316"
  return "#ef4444"
}

function riskLabel(level: RiskLevel) {
  if (level === "very_low") return "Rất thấp"
  if (level === "low") return "Thấp"
  if (level === "moderate") return "Trung bình"
  if (level === "high") return "Cao"
  return "Rất cao"
}

function weatherIcon(point: RouteWeatherResponse["timeline"][number]) {
  const prob = point.precipitation_probability_pct ?? 0
  if (prob >= 80) return "🌧️"
  if (prob >= 60) return "🌦️"
  if (prob >= 40) return "🌥️"
  if (prob >= 20) return "🌤️"
  return "☀️"
}

async function geocodeSearch(q: string) {
  if (!q.trim()) return []
  const data = await $fetch<{ results: GeocodeResult[] }>(`${config.public.apiBaseUrl}/api/geocode`, {
    query: { q, limit: 5 },
  })
  return data.results ?? []
}

const searchOriginDebounced = useDebounceFn(async () => {
  if (originSelected.value && originSelected.value.label === originQuery.value) return
  originSuggestions.value = await geocodeSearch(originQuery.value)
}, 350)

const searchDestinationDebounced = useDebounceFn(async () => {
  if (destinationSelected.value && destinationSelected.value.label === destinationQuery.value) return
  destinationSuggestions.value = await geocodeSearch(destinationQuery.value)
}, 350)

watch(originQuery, (val) => {
  if (originSelected.value && originSelected.value.label === val) return
  originSelected.value = null
  searchOriginDebounced()
})

watch(destinationQuery, (val) => {
  if (destinationSelected.value && destinationSelected.value.label === val) return
  destinationSelected.value = null
  searchDestinationDebounced()
})

function selectOrigin(item: GeocodeResult) {
  originSelected.value = item
  originQuery.value = item.label
  originSuggestions.value = []
}

function selectDestination(item: GeocodeResult) {
  destinationSelected.value = item
  destinationQuery.value = item.label
  destinationSuggestions.value = []
}

async function ensureMap() {
  if (!process.client || map.value || !mapEl.value) return
  maplibreModule = await import("maplibre-gl")
  await import("maplibre-gl/dist/maplibre-gl.css")
  // Wait a tick so the container has layout (important when tab/panel remounts).
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
    // Container may be detached during SSR/hydration races; map still usable.
  }
}

function drawRoute() {
  if (!map.value || !maplibreModule || !routeWeather.value) return
  const m = map.value
  const popup = new maplibreModule.Popup({ offset: 15, closeButton: true, maxWidth: "320px" })
  const segmentByLayer = new Map<string, (typeof routeWeather.value.segments)[number]>()

  // remove old layers/sources
  routeWeather.value.segments.forEach((s) => {
    const id = `seg-${s.index}`
    if (m.getLayer(id)) m.removeLayer(id)
    if (m.getSource(id)) m.removeSource(id)
  })

  routeWeather.value.segments.forEach((s) => {
    const id = `seg-${s.index}`
    segmentByLayer.set(id, s)
    const coords = s.coordinates.map((p) => [p.lng, p.lat])
    m.addSource(id, {
      type: "geojson",
      data: { type: "Feature", geometry: { type: "LineString", coordinates: coords }, properties: {} },
    })
    m.addLayer({
      id,
      source: id,
      type: "line",
      paint: {
        "line-color": riskColor(s.risk_level),
        "line-width": 6,
        "line-opacity": 0.9,
      },
    })

    m.on("click", id, (e) => {
      const seg = segmentByLayer.get(id)
      if (!seg) return
      const prob = seg.weather.precipitation_probability_pct ?? 0
      const temp = seg.weather.temperature_c ?? null
      const wind = seg.weather.wind_speed_kmh ?? null
      const condition = seg.weather.condition ?? "—"

      popup
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="text-sm">
            <div class="font-semibold">${seg.label ?? `Đoạn ${seg.index + 1}`}</div>
            <div class="mt-1 text-xs text-slate-400">${formatTime(seg.arrival_time)}</div>
            <div class="mt-2 flex items-center justify-between">
              <span>${weatherIcon(seg.weather as any) ?? ""}</span>
              <span class="font-semibold">${Math.round(prob)}% · ${condition}</span>
            </div>
            <div class="mt-1 text-xs text-slate-300">${temp !== null ? `${temp}°C` : "—"}${wind !== null ? ` · Gió ${Math.round(wind)} km/h` : ""}</div>
            <div class="mt-2 text-xs">
              <span class="font-semibold">Risk:</span> ${riskLabel(seg.risk_level)}
            </div>
          </div>
        `)
        .addTo(m)
    })

    m.on("mouseenter", id, () => {
      if (m.getCanvas) m.getCanvas().style.cursor = "pointer"
    })
    m.on("mouseleave", id, () => {
      if (m.getCanvas) m.getCanvas().style.cursor = ""
    })
  })

  const first = routeWeather.value.segments[0]?.coordinates[0]
  const lastSeg = routeWeather.value.segments[routeWeather.value.segments.length - 1]
  const last = lastSeg?.coordinates[lastSeg.coordinates.length - 1]

  if (startMarker) startMarker.remove()
  if (endMarker) endMarker.remove()
  if (first) startMarker = new maplibreModule.Marker({ color: "#22c55e" }).setLngLat([first.lng, first.lat]).addTo(m)
  if (last) endMarker = new maplibreModule.Marker({ color: "#ef4444" }).setLngLat([last.lng, last.lat]).addTo(m)

  const allCoords = routeWeather.value.segments.flatMap((s) => s.coordinates.map((p) => [p.lng, p.lat] as [number, number]))
  if (allCoords.length) {
    const bounds = allCoords.reduce((b, c) => b.extend(c), new maplibreModule.LngLatBounds(allCoords[0], allCoords[0]))
    m.fitBounds(bounds, { padding: 40 })
  }
}

async function runRouteWeather() {
  if (!originSelected.value || !destinationSelected.value) return
  loading.value = true
  errorMessage.value = ""
  try {
    const depIso = departureLocal.value + ":00"
    routeWeather.value = await $fetch<RouteWeatherResponse>(`${config.public.apiBaseUrl}/api/route-weather`, {
      method: "POST",
      body: {
        origin: originSelected.value.point,
        destination: destinationSelected.value.point,
        origin_label: originSelected.value.label,
        destination_label: destinationSelected.value.label,
        departure_time: depIso,
        travel_mode: travelMode.value,
        geocode_route_points: true,
      },
    })
    await ensureMap()
    if (map.value?.isStyleLoaded()) drawRoute()
    else map.value?.once("load", drawRoute)
  } catch (e: any) {
    errorMessage.value = e?.data?.detail ?? "Không thể tính lộ trình & thời tiết."
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await $fetch<{ status: string }>(`${config.public.apiBaseUrl}/api/health`)
    healthOk.value = res.status === "ok"
  } catch {
    healthOk.value = false
  }
  await ensureMap()
})
</script>

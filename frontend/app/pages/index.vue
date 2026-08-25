<template>
  <div class="flex h-screen overflow-hidden flex-col md:flex-row">
    <aside class="flex w-full shrink-0 flex-col gap-4 overflow-y-auto border-r border-slate-700/50 p-4 md:w-80">
      <div class="mb-2">
        <h1 class="text-xl font-bold">Route Weather</h1>
        <p class="mt-1 text-xs text-slate-400">Biết thời tiết trên từng chặng đường</p>
      </div>

      <RouteForm
        v-model:origin-query="originQuery"
        v-model:destination-query="destinationQuery"
        v-model:travel-mode="travelMode"
        v-model:departure-local="departureLocal"
        :origin-suggestions="originSuggestions"
        :destination-suggestions="destinationSuggestions"
        :loading="loading"
        :loading-message="loadingMessage"
        :error-message="errorMessage"
        :weather-warning="weatherWarning"
        :can-submit="!!originSelected && !!destinationSelected"
        @select-origin="selectOrigin"
        @select-destination="selectDestination"
        @analyze="analyze"
      />

      <JourneySummary
        :distance-km="routeWeather?.route.distance_km ?? null"
        :duration-minutes="routeWeather?.route.duration_minutes ?? null"
        :departure-display="departureDisplay"
        :eta-display="etaDisplay"
      />

      <RadarControls
        :enabled="radarEnabled"
        :opacity="radarOpacity"
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
        :nowcasting-enabled="nowcastingEnabled"
        :nowcasting-loading="nowcastingLoading"
        :nowcasting-error="nowcastingError"
        :nowcasting-model-label="nowcastingModelLabel"
        :selected-horizon="selectedHorizon"
        :nowcast-prediction-count="nowcastPredictionCountDisplay"
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
        @update:nowcasting-enabled="setNowcastingEnabled"
        @update:selected-horizon="setHorizon"
        @update:satellite-enabled="setSatelliteEnabled"
        @update:satellite-opacity="setSatelliteOpacity"
        @refresh="onRefreshLayers"
      />

      <FusionDebugPanel
        :enabled="fusionDebugEnabled"
        :loading="fusionLoading"
        :error-message="fusionError"
        :state="fusionState"
        :can-refresh="fusionCanRefresh"
        @refresh="refreshFusionDebug"
      />

      <p class="text-xs" :class="healthOk ? 'text-green-400' : 'text-red-400'">
        API {{ healthOk ? "online" : "offline" }}
      </p>
    </aside>

    <main class="flex flex-1 flex-col overflow-hidden">
      <div class="relative min-h-[50vh] flex-1">
        <ClientOnly>
          <RouteMap
            :route-weather="routeWeather"
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
            :nowcasting-enabled="nowcastingEnabled"
            :selected-horizon="selectedHorizon"
            :predicted-cells="predictionsForHorizon"
            :nowcast-model="nowcastResponse?.model ?? null"
          />
        </ClientOnly>
      </div>
      <WeatherTimeline :points="routeWeather?.timeline ?? []" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useNowcasting } from "~/composables/useNowcasting"
import { useRainCells } from "~/composables/useRainCells"
import { useSatellite } from "~/composables/useSatellite"
import { useWeatherFusion } from "~/composables/useWeatherFusion"
import { nowcastModelLabel } from "~/utils/nowcast"

const {
  healthOk,
  loading,
  loadingMessage,
  errorMessage,
  weatherWarning,
  originQuery,
  destinationQuery,
  originSuggestions,
  destinationSuggestions,
  originSelected,
  destinationSelected,
  travelMode,
  departureLocal,
  routeWeather,
  checkHealth,
  selectOrigin,
  selectDestination,
  analyze,
} = useRouteWeather()

const {
  enabled: radarEnabled,
  opacity: radarOpacity,
  loading: radarLoading,
  errorMessage: radarError,
  frame: radarFrame,
  freshnessLabel: radarFreshness,
  timestampDisplay: radarTimestamp,
  fetchRadar,
  setEnabled: setRadarEnabled,
  setOpacity: setRadarOpacity,
} = useRadar()

const {
  enabled: rainCellsEnabled,
  loading: rainCellsLoading,
  errorMessage: rainCellsError,
  cells: trackedCells,
  cellCount,
  response: rainCellsResponse,
  fetchRainCells,
  setEnabled: setRainCellsEnabled,
} = useRainCells()

const {
  enabled: nowcastingEnabled,
  selectedHorizon,
  loading: nowcastingLoading,
  errorMessage: nowcastingError,
  response: nowcastResponse,
  predictionsForHorizon,
  fetchNowcast,
  setEnabled: setNowcastingEnabled,
  setHorizon,
} = useNowcasting()

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
  setOpacity: setSatelliteOpacity,
} = useSatellite()

const {
  enabled: fusionDebugEnabled,
  loading: fusionLoading,
  errorMessage: fusionError,
  state: fusionState,
  fetchFusion,
} = useWeatherFusion()

const routeGeometry = computed(() => {
  if (!routeWeather.value?.segments) return null
  return routeWeather.value.segments.flatMap((s) => s.coordinates ?? [])
})

const routeReady = computed(() => (routeGeometry.value?.length ?? 0) >= 2)
const rainCellCountDisplay = computed(() => (rainCellsEnabled.value && routeReady.value ? cellCount.value : null))
const rainCellsFramesUsed = computed(() => rainCellsResponse.value?.frames_used ?? null)
const nowcastingModelLabel = computed(() =>
  nowcastResponse.value?.model ? nowcastModelLabel(nowcastResponse.value.model) : null,
)
const nowcastPredictionCountDisplay = computed(() => {
  if (!nowcastingEnabled.value || !routeReady.value) return null
  const preds = nowcastResponse.value?.predictions ?? []
  return new Set(preds.map((p) => p.cell_id)).size
})

function onRefreshLayers() {
  void fetchRadar()
  void fetchSatellite()
  if (rainCellsEnabled.value && routeGeometry.value) {
    void fetchRainCells(routeGeometry.value)
  }
  if (nowcastingEnabled.value && routeGeometry.value) {
    void fetchNowcast(routeGeometry.value)
  }
  if (fusionCanRefresh.value) {
    void refreshFusionDebug()
  }
}

watch([routeGeometry, rainCellsEnabled], ([geom, enabled]) => {
  if (enabled && geom && geom.length >= 2) {
    void fetchRainCells(geom)
  }
})

watch([routeGeometry, nowcastingEnabled], ([geom, enabled]) => {
  if (enabled && geom && geom.length >= 2) {
    void fetchNowcast(geom)
  }
})

const radarTileUrl = computed(() =>
  radarEnabled.value && radarFrame.value?.tile_url_template ? radarFrame.value.tile_url_template : null,
)
const radarTileMaxZoom = computed(() => radarFrame.value?.tile_max_zoom ?? 7)
const satelliteTileUrl = computed(() =>
  satelliteEnabled.value && satelliteFrame.value?.tile_url_template ? satelliteFrame.value.tile_url_template : null,
)
const satelliteTileMaxZoom = computed(() => satelliteFrame.value?.tile_max_zoom ?? 6)

const departureDisplay = computed(() => (departureLocal.value ? departureLocal.value.slice(11, 16) : "—"))
const fusionCanRefresh = computed(
  () => Boolean(routeWeather.value && originSelected.value && destinationSelected.value && departureLocal.value),
)

async function refreshFusionDebug() {
  if (!fusionCanRefresh.value || !originSelected.value || !destinationSelected.value) return
  await fetchFusion({
    origin: originSelected.value.point,
    destination: destinationSelected.value.point,
    departure_time: `${departureLocal.value}:00`,
    travel_mode: travelMode.value,
    include_rain_cells: rainCellsEnabled.value,
  })
}

const etaDisplay = computed(() => {
  if (!routeWeather.value) return "—"
  const dep = new Date(departureLocal.value)
  dep.setMinutes(dep.getMinutes() + Math.round(routeWeather.value.route.duration_minutes))
  return dep.toTimeString().slice(0, 5)
})

onMounted(() => {
  checkHealth()
})

watch(
  [routeWeather, rainCellsEnabled, radarEnabled, satelliteEnabled],
  () => {
    if (!fusionDebugEnabled.value || !fusionCanRefresh.value) return
    void refreshFusionDebug()
  },
  { deep: true },
)
</script>

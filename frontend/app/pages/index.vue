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
        @update:enabled="setRadarEnabled"
        @update:opacity="setRadarOpacity"
        @refresh="fetchRadar"
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
          />
        </ClientOnly>
      </div>
      <WeatherTimeline :points="routeWeather?.timeline ?? []" />
    </main>
  </div>
</template>

<script setup lang="ts">
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

const radarTileUrl = computed(() =>
  radarEnabled.value && radarFrame.value?.tile_url_template ? radarFrame.value.tile_url_template : null,
)

const departureDisplay = computed(() => (departureLocal.value ? departureLocal.value.slice(11, 16) : "—"))
const etaDisplay = computed(() => {
  if (!routeWeather.value) return "—"
  const dep = new Date(departureLocal.value)
  dep.setMinutes(dep.getMinutes() + Math.round(routeWeather.value.route.duration_minutes))
  return dep.toTimeString().slice(0, 5)
})

onMounted(() => {
  checkHealth()
})
</script>

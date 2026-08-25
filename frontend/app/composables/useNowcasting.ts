import type { LatLng } from "~/types/routeWeather"
import type {
  NowcastPredictionResponse,
  NowcastSelectedHorizon,
  PredictedRainCell,
} from "~/types/nowcasting"

export function useNowcasting() {
  const config = useRuntimeConfig()
  const enabled = useState("nowcast-enabled", () => false)
  const selectedHorizon = useState<NowcastSelectedHorizon>("nowcast-horizon", () => 0)
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)
  const response = ref<NowcastPredictionResponse | null>(null)

  let refreshTimer: ReturnType<typeof setInterval> | null = null

  function clearRefreshTimer() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  function scheduleRefresh(intervalSeconds: number) {
    clearRefreshTimer()
    if (!enabled.value) return
    refreshTimer = setInterval(() => {
      void fetchNowcast(lastGeometry.value, { silent: true })
    }, intervalSeconds * 1000)
  }

  const lastGeometry = ref<LatLng[] | null>(null)

  async function fetchNowcast(geometry: LatLng[] | null, options: { silent?: boolean } = {}) {
    if (!enabled.value || !geometry || geometry.length < 2) {
      response.value = null
      return
    }

    lastGeometry.value = geometry
    if (!options.silent) loading.value = true
    if (!options.silent) errorMessage.value = null

    try {
      const data = await $fetch<NowcastPredictionResponse>(
        `${config.public.apiBaseUrl}/api/nowcasting/predict`,
        {
          method: "POST",
          body: { geometry },
        },
      )
      response.value = data

      if (data.status === "unavailable") {
        errorMessage.value = data.message ?? "Không thể dự báo mưa."
      } else {
        errorMessage.value = data.status === "partial" ? (data.message ?? null) : null
        scheduleRefresh(300)
      }
    } catch {
      response.value = null
      errorMessage.value = "Không thể dự báo mưa."
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  function setEnabled(value: boolean) {
    enabled.value = value
    if (!value) {
      clearRefreshTimer()
      response.value = null
      errorMessage.value = null
      lastGeometry.value = null
    } else if (lastGeometry.value) {
      void fetchNowcast(lastGeometry.value)
    }
  }

  function setHorizon(value: NowcastSelectedHorizon) {
    selectedHorizon.value = value
  }

  const predictionsForHorizon = computed<PredictedRainCell[]>(() => {
    if (selectedHorizon.value === 0) return []
    return (response.value?.predictions ?? []).filter(
      (p) => p.forecast_minutes === selectedHorizon.value,
    )
  })

  onBeforeUnmount(() => clearRefreshTimer())

  return {
    enabled,
    selectedHorizon,
    loading,
    errorMessage,
    response,
    predictionsForHorizon,
    fetchNowcast,
    setEnabled,
    setHorizon,
  }
}

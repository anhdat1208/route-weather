import type { LatLng } from "~/types/routeWeather"
import type {
  TrafficPrediction,
  TrafficPredictionResponse,
  TrafficSelectedHorizon,
} from "~/types/traffic"

export function useTraffic() {
  const config = useRuntimeConfig()
  const enabled = useState("traffic-enabled", () => false)
  const predictionEnabled = useState("traffic-prediction-enabled", () => false)
  const selectedHorizon = useState<TrafficSelectedHorizon>("traffic-horizon", () => 0)
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)
  const response = ref<TrafficPredictionResponse | null>(null)

  let refreshTimer: ReturnType<typeof setInterval> | null = null
  const lastGeometry = ref<LatLng[] | null>(null)

  function isActive() {
    return enabled.value || predictionEnabled.value
  }

  function clearRefreshTimer() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  function clearState() {
    clearRefreshTimer()
    response.value = null
    errorMessage.value = null
    lastGeometry.value = null
  }

  function scheduleRefresh(intervalSeconds: number) {
    clearRefreshTimer()
    if (!isActive()) return
    refreshTimer = setInterval(() => {
      void fetchTraffic(lastGeometry.value, { silent: true })
    }, intervalSeconds * 1000)
  }

  async function fetchTraffic(geometry: LatLng[] | null, options: { silent?: boolean } = {}) {
    if (!isActive() || !geometry || geometry.length < 2) {
      response.value = null
      return
    }

    lastGeometry.value = geometry
    if (!options.silent) loading.value = true
    if (!options.silent) errorMessage.value = null

    try {
      const data = await $fetch<TrafficPredictionResponse>(
        `${config.public.apiBaseUrl}/api/traffic/prediction`,
        {
          method: "POST",
          body: { geometry },
        },
      )
      response.value = data

      if (data.status === "unavailable") {
        errorMessage.value = data.message ?? "Không thể dự báo giao thông."
      } else {
        errorMessage.value = null
        scheduleRefresh(300)
      }
    } catch {
      response.value = null
      errorMessage.value = "Không thể dự báo giao thông."
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  function setEnabled(value: boolean) {
    enabled.value = value
    if (!isActive()) {
      clearState()
    } else if (lastGeometry.value) {
      void fetchTraffic(lastGeometry.value)
    }
  }

  function setPredictionEnabled(value: boolean) {
    predictionEnabled.value = value
    if (!isActive()) {
      clearState()
    } else if (lastGeometry.value) {
      void fetchTraffic(lastGeometry.value)
    }
  }

  function setHorizon(value: TrafficSelectedHorizon) {
    selectedHorizon.value = value
  }

  const predictionsForHorizon = computed<TrafficPrediction[]>(() => {
    if (selectedHorizon.value === 0) return []
    return (response.value?.predictions ?? []).filter(
      (p) => p.forecast_minutes === selectedHorizon.value,
    )
  })

  onBeforeUnmount(() => clearRefreshTimer())

  return {
    enabled,
    predictionEnabled,
    selectedHorizon,
    loading,
    errorMessage,
    response,
    predictionsForHorizon,
    fetchTraffic,
    setEnabled,
    setPredictionEnabled,
    setHorizon,
  }
}

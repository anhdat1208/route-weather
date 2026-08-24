import type { LatLng } from "~/types/routeWeather"
import type { RainCellTrackResponse, TrackedRainCell } from "~/types/rainCell"

export function useRainCells() {
  const config = useRuntimeConfig()
  const enabled = useState("rain-cells-enabled", () => false)
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)
  const response = ref<RainCellTrackResponse | null>(null)

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
      void fetchRainCells(lastGeometry.value, { silent: true })
    }, intervalSeconds * 1000)
  }

  const lastGeometry = ref<LatLng[] | null>(null)

  async function fetchRainCells(geometry: LatLng[] | null, options: { silent?: boolean } = {}) {
    if (!enabled.value || !geometry || geometry.length < 2) {
      response.value = null
      return
    }

    lastGeometry.value = geometry
    if (!options.silent) loading.value = true
    if (!options.silent) errorMessage.value = null

    try {
      const data = await $fetch<RainCellTrackResponse>(`${config.public.apiBaseUrl}/api/rain-cells/track`, {
        method: "POST",
        body: { geometry },
      })
      response.value = data

      if (data.status === "unavailable") {
        errorMessage.value = data.message ?? "Không thể phân tích vùng mưa."
      } else {
        errorMessage.value = data.status === "partial" ? (data.message ?? null) : null
        scheduleRefresh(300)
      }
    } catch {
      response.value = null
      errorMessage.value = "Không thể phân tích vùng mưa."
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
      void fetchRainCells(lastGeometry.value)
    }
  }

  const cells = computed<TrackedRainCell[]>(() => response.value?.cells ?? [])

  const cellCount = computed(() => cells.value.filter((c) => c.state !== "LOST").length)

  onBeforeUnmount(() => clearRefreshTimer())

  return {
    enabled,
    loading,
    errorMessage,
    response,
    cells,
    cellCount,
    fetchRainCells,
    setEnabled,
  }
}

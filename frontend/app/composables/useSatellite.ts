import type { SatelliteFrameResponse } from "~/types/satellite"

const DEFAULT_OPACITY = 0.45
const DEFAULT_ENABLED = false

export function useSatellite() {
  const config = useRuntimeConfig()
  const enabled = useState("satellite-enabled", () => DEFAULT_ENABLED)
  const opacity = useState("satellite-opacity", () => DEFAULT_OPACITY)
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)
  const frame = ref<SatelliteFrameResponse | null>(null)

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
      void fetchSatellite({ silent: true })
    }, intervalSeconds * 1000)
  }

  async function fetchSatellite(options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    if (!options.silent) errorMessage.value = null
    try {
      const data = await $fetch<SatelliteFrameResponse>(`${config.public.apiBaseUrl}/api/satellite/latest`)
      frame.value = data
      if (data.status === "unavailable") {
        errorMessage.value = data.message ?? "Dữ liệu vệ tinh tạm thời không khả dụng."
      } else {
        errorMessage.value = data.status === "stale" ? (data.message ?? "Dữ liệu vệ tinh có thể đã cũ.") : null
        scheduleRefresh(data.refresh_interval_seconds)
      }
    } catch {
      frame.value = null
      errorMessage.value = "Dữ liệu vệ tinh tạm thời không khả dụng."
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  function setEnabled(value: boolean) {
    enabled.value = value
    if (value && !frame.value) {
      void fetchSatellite()
    }
    if (value && frame.value) {
      scheduleRefresh(frame.value.refresh_interval_seconds)
    }
    if (!value) clearRefreshTimer()
  }

  function setOpacity(value: number) {
    opacity.value = Math.min(1, Math.max(0.1, value))
  }

  const freshnessLabel = computed(() => {
    if (!frame.value?.observed_at) return null
    const ts = new Date(frame.value.observed_at)
    const ageMinutes = Math.max(0, Math.round((Date.now() - ts.getTime()) / 60000))
    if (ageMinutes === 0) return "Vừa cập nhật"
    return `Cập nhật ${ageMinutes} phút trước`
  })

  const timestampDisplay = computed(() => {
    if (!frame.value?.observed_at) return null
    const ts = new Date(frame.value.observed_at)
    return ts.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Bangkok" })
  })

  onMounted(() => {
    if (enabled.value) void fetchSatellite()
  })
  onBeforeUnmount(() => clearRefreshTimer())

  return {
    enabled,
    opacity,
    loading,
    errorMessage,
    frame,
    freshnessLabel,
    timestampDisplay,
    fetchSatellite,
    setEnabled,
    setOpacity,
  }
}

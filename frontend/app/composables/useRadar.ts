import type { RadarFrameResponse } from "~/types/radar"

const DEFAULT_OPACITY = 0.65
const DEFAULT_ENABLED = true

export function useRadar() {
  const config = useRuntimeConfig()

  const enabled = useState("radar-enabled", () => DEFAULT_ENABLED)
  const opacity = useState("radar-opacity", () => DEFAULT_OPACITY)
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)
  const frame = ref<RadarFrameResponse | null>(null)

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
      void fetchRadar({ silent: true })
    }, intervalSeconds * 1000)
  }

  async function fetchRadar(options: { silent?: boolean } = {}) {
    if (!options.silent) loading.value = true
    if (!options.silent) errorMessage.value = null

    try {
      const data = await $fetch<RadarFrameResponse>(`${config.public.apiBaseUrl}/api/radar/current`)
      frame.value = data

      if (data.status === "unavailable") {
        errorMessage.value = data.message ?? "Dữ liệu radar tạm thời không khả dụng."
      } else {
        errorMessage.value = data.status === "stale" ? (data.message ?? "Dữ liệu radar có thể đã cũ.") : null
        scheduleRefresh(data.refresh_interval_seconds)
      }
    } catch {
      frame.value = null
      errorMessage.value = "Dữ liệu radar tạm thời không khả dụng."
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  function setEnabled(value: boolean) {
    enabled.value = value
    if (value && !frame.value) {
      void fetchRadar()
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
    if (!frame.value?.timestamp) return null
    const ts = new Date(frame.value.timestamp)
    const ageMinutes = Math.max(0, Math.round((Date.now() - ts.getTime()) / 60000))
    if (ageMinutes === 0) return "Vừa cập nhật"
    return `Cập nhật ${ageMinutes} phút trước`
  })

  const timestampDisplay = computed(() => {
    if (!frame.value?.timestamp) return null
    const ts = new Date(frame.value.timestamp)
    return ts.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Bangkok" })
  })

  onMounted(() => {
    if (enabled.value) void fetchRadar()
  })

  onBeforeUnmount(() => {
    clearRefreshTimer()
  })

  return {
    enabled,
    opacity,
    loading,
    errorMessage,
    frame,
    freshnessLabel,
    timestampDisplay,
    fetchRadar,
    setEnabled,
    setOpacity,
  }
}

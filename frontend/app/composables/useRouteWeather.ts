import { useDebounceFn } from "@vueuse/core"
import type {
  GeocodeResult,
  LoadingPhase,
  RouteWeatherResponse,
  TravelMode,
} from "~/types/routeWeather"

function toLocalDateTimeInputValue(date: Date) {
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function useRouteWeather() {
  const config = useRuntimeConfig()
  const healthOk = ref(false)
  const loading = ref(false)
  const loadingPhase = ref<LoadingPhase>("idle")
  const errorMessage = ref("")
  const weatherWarning = ref("")

  const originQuery = ref("")
  const destinationQuery = ref("")
  const originSuggestions = ref<GeocodeResult[]>([])
  const destinationSuggestions = ref<GeocodeResult[]>([])
  const originSelected = ref<GeocodeResult | null>(null)
  const destinationSelected = ref<GeocodeResult | null>(null)
  const travelMode = ref<TravelMode>("motorbike")
  const departureLocal = ref(toLocalDateTimeInputValue(new Date(Date.now() + 15 * 60 * 1000)))
  const routeWeather = ref<RouteWeatherResponse | null>(null)

  async function checkHealth() {
    try {
      const res = await $fetch<{ status: string }>(`${config.public.apiBaseUrl}/api/health`)
      healthOk.value = res.status === "ok"
    } catch {
      healthOk.value = false
    }
  }

  async function geocodeSearch(q: string) {
    if (!q.trim()) return [] as GeocodeResult[]
    try {
      const data = await $fetch<{ results: GeocodeResult[] }>(`${config.public.apiBaseUrl}/api/geocode`, {
        query: { q, limit: 5 },
      })
      return data.results ?? []
    } catch {
      return []
    }
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

  async function analyze() {
    if (!originSelected.value || !destinationSelected.value) {
      errorMessage.value = "Vui lòng chọn điểm đi và điểm đến hợp lệ."
      return
    }
    loading.value = true
    loadingPhase.value = "routing"
    errorMessage.value = ""
    weatherWarning.value = ""
    try {
      loadingPhase.value = "weather"
      const depIso = departureLocal.value + ":00"
      const data = await $fetch<RouteWeatherResponse>(`${config.public.apiBaseUrl}/api/route-weather`, {
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
      routeWeather.value = data
      if (data.weather_status === "unavailable") {
        weatherWarning.value = "Lộ trình đã tính được. Thời tiết tạm thời không khả dụng."
      } else if (data.weather_status === "partial") {
        weatherWarning.value = "Một số điểm thời tiết tạm thời không khả dụng."
      }
      loadingPhase.value = "done"
    } catch (e: any) {
      const detail = e?.data?.detail
      errorMessage.value = typeof detail === "string" ? detail : "Không tìm được lộ trình hoặc địa chỉ không hợp lệ."
      routeWeather.value = null
      loadingPhase.value = "idle"
    } finally {
      loading.value = false
    }
  }

  const loadingMessage = computed(() => {
    if (loadingPhase.value === "routing") return "Đang tính lộ trình..."
    if (loadingPhase.value === "weather") return "Đang phân tích thời tiết trên hành trình..."
    return ""
  })

  return {
    healthOk,
    loading,
    loadingPhase,
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
  }
}

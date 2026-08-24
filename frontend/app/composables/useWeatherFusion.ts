import type { LatLng, TravelMode } from "~/types/routeWeather"
import type { WeatherFusionRequest, WeatherFusionResponse } from "~/types/fusion"

type FusionParams = {
  origin: LatLng
  destination: LatLng
  departure_time: string
  travel_mode: TravelMode
  include_rain_cells?: boolean
}

export function useWeatherFusion() {
  const config = useRuntimeConfig()
  const loading = ref(false)
  const errorMessage = ref<string | null>(null)
  const state = ref<WeatherFusionResponse | null>(null)
  const enabled = computed(() => Boolean(import.meta.dev || config.public.enableFusionDebug))

  async function fetchFusion(params: FusionParams, options: { silent?: boolean } = {}) {
    if (!enabled.value) return
    if (!options.silent) {
      loading.value = true
      errorMessage.value = null
    }
    try {
      const body: WeatherFusionRequest = {
        ...params,
        include_rain_cells: params.include_rain_cells ?? true,
      }
      state.value = await $fetch<WeatherFusionResponse>(`${config.public.apiBaseUrl}/api/weather-fusion/state`, {
        method: "POST",
        body,
      })
    } catch {
      errorMessage.value = "Không lấy được dữ liệu fusion debug."
      state.value = null
    } finally {
      if (!options.silent) loading.value = false
    }
  }

  return {
    enabled,
    loading,
    errorMessage,
    state,
    fetchFusion,
  }
}

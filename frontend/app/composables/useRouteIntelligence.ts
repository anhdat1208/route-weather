import type {
  RouteIntelligenceCompareResponse,
  RouteIntelligenceRequest,
  RouteIntelligenceResponse,
} from "~/types/routeIntelligence"

export function useRouteIntelligence() {
  const config = useRuntimeConfig()
  const loading = ref(false)
  const errorMessage = ref("")
  const intelligence = ref<RouteIntelligenceResponse | null>(null)
  const selectedSegmentId = ref<string | null>(null)
  const departureCompare = ref<RouteIntelligenceCompareResponse | null>(null)
  const compareLoading = ref(false)

  async function analyze(request: RouteIntelligenceRequest) {
    loading.value = true
    errorMessage.value = ""
    try {
      intelligence.value = await $fetch<RouteIntelligenceResponse>(
        `${config.public.apiBaseUrl}/api/route-intelligence/analyze`,
        { method: "POST", body: request },
      )
      selectedSegmentId.value = intelligence.value.summary.worst_segment_id
    } catch (e: any) {
      const detail = e?.data?.detail
      errorMessage.value =
        typeof detail === "string" ? detail : "Phân tích Route Intelligence thất bại."
      intelligence.value = null
    } finally {
      loading.value = false
    }
  }

  async function compareDepartures(request: RouteIntelligenceRequest, offsets: number[] = [0, 30, 60]) {
    compareLoading.value = true
    try {
      departureCompare.value = await $fetch<RouteIntelligenceCompareResponse>(
        `${config.public.apiBaseUrl}/api/route-intelligence/compare`,
        {
          method: "POST",
          body: { request, offsets_minutes: offsets },
        },
      )
      if (departureCompare.value?.baseline) {
        intelligence.value = departureCompare.value.baseline
      }
    } catch {
      departureCompare.value = null
    } finally {
      compareLoading.value = false
    }
  }

  function selectSegment(id: string | null) {
    selectedSegmentId.value = id
  }

  const selectedSegment = computed(() => {
    if (!intelligence.value || !selectedSegmentId.value) return null
    return intelligence.value.segments.find((s) => s.id === selectedSegmentId.value) ?? null
  })

  return {
    loading,
    errorMessage,
    intelligence,
    selectedSegmentId,
    selectedSegment,
    departureCompare,
    compareLoading,
    analyze,
    compareDepartures,
    selectSegment,
  }
}

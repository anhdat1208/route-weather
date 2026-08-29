<template>
  <div v-if="summary" class="rounded-xl border border-slate-700/50 bg-slate-900/40 p-4">
    <h2 class="mb-3 text-sm font-semibold text-slate-200">Route Weather Intelligence</h2>

    <div class="grid grid-cols-2 gap-3 text-sm">
      <div>
        <div class="text-xs text-slate-400">ETA</div>
        <div class="font-medium">{{ etaLabel }}</div>
      </div>
      <div>
        <div class="text-xs text-slate-400">Điểm tuyến</div>
        <div class="font-medium" :style="{ color: scoreColor }">{{ summary.score.toFixed(0) }}/100</div>
      </div>
      <div>
        <div class="text-xs text-slate-400">Rủi ro tổng</div>
        <div class="font-medium" :style="{ color: riskColor }">{{ riskLabel }}</div>
      </div>
      <div>
        <div class="text-xs text-slate-400">Độ tin cậy</div>
        <div class="font-medium">{{ (summary.confidence * 100).toFixed(0) }}%</div>
      </div>
    </div>

    <div class="mt-3 space-y-1 text-xs text-slate-300">
      <p><span class="text-slate-400">Thời tiết:</span> {{ summary.weather_summary }}</p>
      <p><span class="text-slate-400">Giao thông:</span> {{ summary.traffic_summary }}</p>
      <p v-if="summary.worst_segment_id || summary.worst_segment_label">
        <span class="text-slate-400">Đoạn xấu nhất:</span>
        {{ summary.worst_segment_label || summary.worst_segment_id }}
        <span v-if="summary.worst_condition"> — {{ summary.worst_condition }}</span>
      </p>
    </div>

    <div v-if="recommendation" class="mt-3 rounded-lg bg-slate-800/60 p-3 text-xs text-slate-200">
      <p class="font-medium">{{ recommendation.message }}</p>
      <ul v-if="recommendation.details.length" class="mt-2 list-inside list-disc text-slate-400">
        <li v-for="(d, i) in recommendation.details" :key="`rec-${i}`">{{ d }}</li>
      </ul>
    </div>

    <div v-if="explainability?.main_contributors?.length" class="mt-3 text-xs text-slate-400">
      <p class="mb-1 font-medium text-slate-300">Nguyên nhân chính</p>
      <ul class="list-inside list-disc">
        <li v-for="(c, i) in explainability.main_contributors.slice(0, 4)" :key="`exp-${i}`">{{ c }}</li>
      </ul>
    </div>

    <div v-if="departureAlternatives.length > 1" class="mt-3">
      <p class="mb-2 text-xs font-medium text-slate-300">So sánh giờ xuất phát</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="alt in departureAlternatives"
          :key="`dep-${alt.offset_minutes}`"
          type="button"
          class="rounded-lg border px-2 py-1 text-xs transition"
          :class="
            alt.offset_minutes === 0
              ? 'border-sky-500/50 bg-sky-500/10 text-sky-200'
              : 'border-slate-600 text-slate-300 hover:border-slate-500'
          "
        >
          {{ formatTime(alt.departure_time) }} · {{ alt.score.toFixed(0) }}/100
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type {
  DepartureAlternative,
  RouteIntelExplainability,
  RouteIntelRecommendation,
  RouteIntelSummary,
} from "~/types/routeIntelligence"
import { formatTime, riskBandColor, riskBandLabel } from "~/utils/routeIntelligence"

const props = defineProps<{
  summary: RouteIntelSummary | null
  recommendation: RouteIntelRecommendation | null
  explainability: RouteIntelExplainability | null
  departureAlternatives?: DepartureAlternative[]
  etaLabel?: string
}>()

const riskColor = computed(() => (props.summary ? riskBandColor(props.summary.risk_level) : "#64748b"))
const riskLabel = computed(() => (props.summary ? riskBandLabel(props.summary.risk_level) : "—"))
const scoreColor = computed(() => {
  if (!props.summary) return "#64748b"
  if (props.summary.score >= 70) return "#22c55e"
  if (props.summary.score >= 50) return "#eab308"
  return "#f97316"
})

const departureAlternatives = computed(() => props.departureAlternatives ?? [])
</script>

<template>
  <div class="border-t border-slate-700/50 p-4">
    <h2 class="mb-3 text-sm font-semibold text-slate-200">Timeline thông minh</h2>
    <div v-if="segments.length" class="flex items-stretch gap-2 overflow-x-auto pb-2">
      <button
        v-for="seg in segments"
        :key="seg.id"
        type="button"
        class="min-w-[160px] rounded-xl border px-3 py-2 text-left transition"
        :class="
          selectedId === seg.id
            ? 'border-sky-500/60 bg-sky-500/10'
            : 'border-slate-700/50 bg-slate-900/40 hover:border-slate-600'
        "
        @click="$emit('select', seg.id)"
      >
        <div class="text-xs text-slate-400">{{ formatTime(seg.arrival_time) }}</div>
        <div class="mt-1 text-sm font-medium">{{ seg.label || seg.id }}</div>

        <div class="mt-2 flex items-center justify-between text-xs">
          <span :style="{ color: riskBandColor(seg.risk.travel_risk_level) }">
            {{ riskBandLabel(seg.risk.travel_risk_level) }}
          </span>
          <span class="text-slate-400">{{ seg.weather.rain_probability_pct ?? 0 }}%</span>
        </div>

        <div class="mt-2 text-xs text-slate-300">
          {{ rainStatusLabel(seg.weather.rain_status) }}
        </div>
        <div v-if="seg.traffic" class="mt-1 text-xs text-slate-400">
          Giao thông: {{ congestionLabel(seg.traffic.predicted_congestion) }}
        </div>
        <div class="mt-1 text-[11px] text-slate-500">
          Tin cậy: {{ (seg.risk.confidence * 100).toFixed(0) }}%
        </div>
      </button>
    </div>
    <div v-else class="text-sm text-slate-500">Chưa có dữ liệu intelligence.</div>
  </div>
</template>

<script setup lang="ts">
import type { RouteIntelligenceSegment } from "~/types/routeIntelligence"
import {
  congestionLabel,
  formatTime,
  rainStatusLabel,
  riskBandColor,
  riskBandLabel,
} from "~/utils/routeIntelligence"

defineProps<{
  segments: RouteIntelligenceSegment[]
  selectedId: string | null
}>()

defineEmits<{ select: [id: string] }>()
</script>

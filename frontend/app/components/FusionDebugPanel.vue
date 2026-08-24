<template>
  <div v-if="enabled" class="card space-y-3 text-xs">
    <div class="flex items-center justify-between gap-2">
      <h3 class="font-semibold text-slate-200">Fusion debug</h3>
      <button
        type="button"
        class="text-[11px] text-slate-400 underline-offset-2 hover:text-slate-200 hover:underline disabled:opacity-50"
        :disabled="loading || !canRefresh"
        @click="$emit('refresh')"
      >
        Làm mới
      </button>
    </div>

    <div v-if="loading" class="text-slate-400">Đang lấy weather-fusion state…</div>
    <div v-else-if="errorMessage" class="text-amber-400">{{ errorMessage }}</div>
    <div v-else-if="!state" class="text-slate-500">Chưa có dữ liệu fusion.</div>
    <div v-else class="space-y-2">
      <div class="rounded border border-slate-700/50 bg-slate-900/40 p-2">
        <div>Observed: {{ fmtTime(state.observed_at) }}</div>
        <div>Route: {{ state.route_distance_km.toFixed(1) }} km · {{ Math.round(state.route_duration_minutes) }} phút</div>
      </div>

      <div class="max-h-52 space-y-2 overflow-y-auto pr-1">
        <div v-for="seg in state.segments" :key="seg.segment_index" class="rounded border border-slate-700/50 p-2">
          <div class="font-medium text-slate-200">
            Segment {{ seg.segment_index + 1 }} · {{ fmtTime(seg.arrival_time) }}
            · tin cậy {{ Math.round(seg.confidence * 100) }}%
          </div>
          <div class="mt-1 text-[11px] text-slate-300">
            Forecast: <span :class="qualityClass(seg.data_quality.forecast)">{{ seg.data_quality.forecast }}</span> ·
            Radar: <span :class="qualityClass(seg.data_quality.radar)">{{ seg.data_quality.radar }}</span> ·
            Satellite: <span :class="qualityClass(seg.data_quality.satellite)">{{ seg.data_quality.satellite }}</span> ·
            RainCell: <span :class="qualityClass(seg.data_quality.rain_cell)">{{ seg.data_quality.rain_cell }}</span>
          </div>
          <div class="mt-1 text-[11px] text-slate-400">
            Radar ts: {{ fmtTime(seg.radar_meta?.observed_at) }} · Satellite ts: {{ fmtTime(seg.satellite_meta?.observed_at) }}
          </div>
          <div v-if="seg.data_quality.conflicts.length" class="mt-1 text-[11px] text-amber-300">
            Conflict: {{ seg.data_quality.conflicts.join(", ") }}
          </div>
          <div v-if="seg.rain_cell" class="mt-1 text-[11px] text-slate-400">
            Rain cells: {{ seg.rain_cell.count }} · nearest {{ seg.rain_cell.nearest_distance_km ?? "?" }} km
            <span v-if="seg.rain_cell.corridor_overlap != null"> · overlap {{ seg.rain_cell.corridor_overlap }}</span>
          </div>
          <div class="mt-1 text-[11px] text-slate-500">
            Evidence: {{ seg.features.precip_evidence ? "có mưa gần corridor" : "không" }}
            · Δ radar/sat {{ seg.features.radar_satellite_delta_seconds ?? "—" }}s
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WeatherFusionResponse, DataQuality } from "~/types/fusion"

defineProps<{
  enabled: boolean
  loading: boolean
  errorMessage: string | null
  state: WeatherFusionResponse | null
  canRefresh: boolean
}>()

defineEmits<{
  refresh: []
}>()

function fmtTime(v?: string | null) {
  if (!v) return "—"
  const d = new Date(v)
  return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "Asia/Bangkok" })
}

function qualityClass(q: DataQuality) {
  if (q === "GOOD") return "text-green-400"
  if (q === "STALE" || q === "CONFLICTING") return "text-amber-400"
  if (q === "MISSING") return "text-slate-500"
  return "text-slate-300"
}
</script>

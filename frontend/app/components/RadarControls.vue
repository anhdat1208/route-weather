<template>
  <div class="card space-y-3 text-sm">
    <div class="flex items-center justify-between gap-2">
      <h3 class="font-semibold text-slate-200">Lớp thời tiết</h3>
      <button
        type="button"
        class="text-xs text-slate-400 underline-offset-2 hover:text-slate-200 hover:underline disabled:opacity-50"
        :disabled="loading"
        @click="$emit('refresh')"
      >
        Làm mới
      </button>
    </div>

    <label class="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
        :checked="rainCellsEnabled"
        :disabled="!routeReady"
        @change="onRainCellsToggle"
      />
      <span :class="routeReady ? '' : 'text-slate-500'">Vùng mưa (rain cells)</span>
    </label>
    <p v-if="!routeReady" class="text-[10px] text-slate-500">Cần có lộ trình để phân tích vùng mưa.</p>

    <div v-if="rainCellsEnabled && routeReady" class="space-y-1 text-xs">
      <div v-if="rainCellsLoading" class="text-slate-400">Đang phân tích vùng mưa…</div>
      <div v-else-if="rainCellsError" class="text-amber-400">{{ rainCellsError }}</div>
      <div v-else-if="rainCellCount !== null" class="text-slate-300">
        {{ rainCellCount }} vùng mưa đang theo dõi
        <span v-if="rainCellsFramesUsed"> · {{ rainCellsFramesUsed }} khung radar</span>
      </div>
    </div>

    <label class="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
        :checked="nowcastingEnabled"
        :disabled="!routeReady"
        @change="onNowcastingToggle"
      />
      <span :class="routeReady ? '' : 'text-slate-500'">Nowcasting (dự báo mưa)</span>
    </label>
    <p v-if="!routeReady" class="text-[10px] text-slate-500">Cần có lộ trình để dự báo mưa.</p>

    <div v-if="nowcastingEnabled && routeReady" class="space-y-2">
      <div class="space-y-1 text-xs">
        <div v-if="nowcastingLoading" class="text-slate-400">Đang dự báo mưa…</div>
        <div v-else-if="nowcastingError" class="text-amber-400">{{ nowcastingError }}</div>
        <div v-else-if="nowcastPredictionCount !== null" class="text-slate-300">
          {{ nowcastPredictionCount }} vùng mưa dự báo
        </div>
      </div>

      <div class="flex flex-wrap gap-1">
        <button
          v-for="option in horizonOptions"
          :key="option.value"
          type="button"
          class="rounded border px-2 py-0.5 text-[11px] font-medium"
          :class="
            selectedHorizon === option.value
              ? 'border-blue-500 bg-blue-500/20 text-blue-400'
              : 'border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-200'
          "
          @click="$emit('update:selectedHorizon', option.value)"
        >
          {{ option.label }}
        </button>
      </div>

      <p class="text-[10px] text-slate-500">
        Dự báo baseline — không phải radar quan sát
        <span v-if="nowcastingModelLabel"> · {{ nowcastingModelLabel }}</span>
      </p>
    </div>

    <label class="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
        :checked="trafficEnabled"
        :disabled="!routeReady"
        @change="onTrafficToggle"
      />
      <span :class="routeReady ? '' : 'text-slate-500'">Giao thông</span>
    </label>
    <p v-if="!routeReady" class="text-[10px] text-slate-500">Cần có lộ trình để hiển thị giao thông.</p>

    <label class="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
        :checked="trafficPredictionEnabled"
        :disabled="!routeReady"
        @change="onTrafficPredictionToggle"
      />
      <span :class="routeReady ? '' : 'text-slate-500'">Dự báo giao thông</span>
    </label>
    <p v-if="!routeReady" class="text-[10px] text-slate-500">Cần có lộ trình để dự báo giao thông.</p>

    <div v-if="(trafficEnabled || trafficPredictionEnabled) && routeReady" class="space-y-1 text-xs">
      <div v-if="trafficLoading" class="text-slate-400">Đang dự báo giao thông…</div>
      <div v-else-if="trafficError" class="text-amber-400">{{ trafficError }}</div>
      <div v-else-if="trafficSegmentCount !== null" class="text-slate-300">
        {{ trafficSegmentCount }} đoạn đường đang theo dõi
      </div>
    </div>

    <div v-if="trafficPredictionEnabled && routeReady" class="space-y-2">
      <div class="flex flex-wrap gap-1">
        <button
          v-for="option in trafficHorizonOptions"
          :key="option.value"
          type="button"
          class="rounded border px-2 py-0.5 text-[11px] font-medium"
          :class="
            trafficSelectedHorizon === option.value
              ? 'border-blue-500 bg-blue-500/20 text-blue-400'
              : 'border-slate-600 text-slate-400 hover:border-slate-500 hover:text-slate-200'
          "
          @click="$emit('update:trafficSelectedHorizon', option.value)"
        >
          {{ option.label }}
        </button>
      </div>

      <p class="text-[10px] text-slate-500">
        Dự báo baseline v0.1 — giao thông synthetic (không phải live)
        <span v-if="trafficModelLabel"> · {{ trafficModelLabel }}</span>
      </p>
    </div>

    <label class="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
        :checked="enabled"
        @change="onToggle"
      />
      <span>Radar mưa</span>
    </label>

    <div v-if="enabled" class="space-y-2">
      <label class="block text-xs text-slate-400">
        Độ mờ: {{ Math.round(opacity * 100) }}%
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.05"
          class="mt-1 w-full accent-blue-500"
          :value="opacity"
          @input="onOpacity"
        />
      </label>

      <div v-if="loading" class="text-xs text-slate-400">Đang tải radar…</div>

      <div v-else-if="errorMessage" class="text-xs text-amber-400">{{ errorMessage }}</div>

      <template v-else-if="frame">
        <div class="text-xs" :class="statusClass">
          <span class="font-medium">Radar</span>
          <span v-if="timestampDisplay"> · {{ timestampDisplay }} (UTC+7)</span>
          <span v-if="freshnessLabel"> · {{ freshnessLabel }}</span>
        </div>

        <div v-if="legend" class="space-y-1">
          <p class="text-xs text-slate-400">{{ legend.title }}</p>
          <div class="flex h-3 overflow-hidden rounded-full">
            <div
              v-for="(stop, i) in legend.stops"
              :key="i"
              class="flex-1"
              :style="{ backgroundColor: stop.color }"
              :title="stop.label"
            />
          </div>
          <div class="flex justify-between text-[10px] text-slate-500">
            <span>{{ legend.stops[0]?.label ?? "Nhẹ" }}</span>
            <span>{{ legend.stops?.[legend.stops.length - 1]?.label ?? "Mạnh" }}</span>
          </div>
        </div>
      </template>
    </div>

    <label class="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
        :checked="satelliteEnabled"
        @change="onSatelliteToggle"
      />
      <span>Vệ tinh</span>
    </label>

    <div v-if="satelliteEnabled" class="space-y-2">
      <label class="block text-xs text-slate-400">
        Độ mờ vệ tinh: {{ Math.round(satelliteOpacity * 100) }}%
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.05"
          class="mt-1 w-full accent-blue-500"
          :value="satelliteOpacity"
          @input="onSatelliteOpacity"
        />
      </label>
      <div v-if="satelliteLoading" class="text-xs text-slate-400">Đang tải vệ tinh…</div>
      <div v-else-if="satelliteErrorMessage" class="text-xs text-amber-400">{{ satelliteErrorMessage }}</div>
      <template v-else-if="satelliteTimestampDisplay || satelliteFreshnessLabel">
        <div class="text-xs" :class="satelliteStatusClass">
          <span class="font-medium">Satellite</span>
          <span v-if="satelliteTimestampDisplay"> · {{ satelliteTimestampDisplay }} (UTC+7)</span>
          <span v-if="satelliteFreshnessLabel"> · {{ satelliteFreshnessLabel }}</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NowcastSelectedHorizon } from "~/types/nowcasting"
import type { RadarFrameResponse, RadarLegend } from "~/types/radar"
import type { TrafficSelectedHorizon } from "~/types/traffic"

const props = defineProps<{
  enabled: boolean
  opacity: number
  loading: boolean
  errorMessage: string | null
  frame: RadarFrameResponse | null
  freshnessLabel: string | null
  timestampDisplay: string | null
  rainCellsEnabled: boolean
  rainCellsLoading: boolean
  rainCellsError: string | null
  rainCellCount: number | null
  rainCellsFramesUsed: number | null
  routeReady: boolean
  satelliteEnabled: boolean
  satelliteOpacity: number
  satelliteLoading: boolean
  satelliteErrorMessage: string | null
  satelliteStatus: "ok" | "stale" | "unavailable" | null
  satelliteFreshnessLabel: string | null
  satelliteTimestampDisplay: string | null
  nowcastingEnabled: boolean
  nowcastingLoading: boolean
  nowcastingError: string | null
  nowcastingModelLabel: string | null
  selectedHorizon: NowcastSelectedHorizon
  nowcastPredictionCount: number | null
  trafficEnabled: boolean
  trafficPredictionEnabled: boolean
  trafficLoading: boolean
  trafficError: string | null
  trafficModelLabel: string | null
  trafficSelectedHorizon: TrafficSelectedHorizon
  trafficSegmentCount: number | null
}>()

const emit = defineEmits<{
  "update:enabled": [value: boolean]
  "update:opacity": [value: number]
  "update:rainCellsEnabled": [value: boolean]
  "update:satelliteEnabled": [value: boolean]
  "update:satelliteOpacity": [value: number]
  "update:nowcastingEnabled": [value: boolean]
  "update:selectedHorizon": [value: NowcastSelectedHorizon]
  "update:trafficEnabled": [value: boolean]
  "update:trafficPredictionEnabled": [value: boolean]
  "update:trafficSelectedHorizon": [value: TrafficSelectedHorizon]
  refresh: []
}>()

const horizonOptions: { value: NowcastSelectedHorizon; label: string }[] = [
  { value: 0, label: "NOW" },
  { value: 5, label: "+5m" },
  { value: 10, label: "+10m" },
  { value: 15, label: "+15m" },
  { value: 30, label: "+30m" },
  { value: 60, label: "+60m" },
]

const trafficHorizonOptions: { value: TrafficSelectedHorizon; label: string }[] = [
  { value: 0, label: "NOW" },
  { value: 5, label: "+5m" },
  { value: 10, label: "+10m" },
  { value: 15, label: "+15m" },
  { value: 30, label: "+30m" },
]

const legend = computed<RadarLegend | null>(() => props.frame?.legend ?? null)

const statusClass = computed(() => {
  if (props.frame?.status === "stale") return "text-amber-400"
  if (props.frame?.status === "ok") return "text-green-400"
  return "text-slate-400"
})

const satelliteStatusClass = computed(() => {
  if (props.satelliteStatus === "stale") return "text-amber-400"
  if (props.satelliteStatus === "ok") return "text-green-400"
  return "text-slate-400"
})

function onToggle(event: Event) {
  emit("update:enabled", (event.target as HTMLInputElement).checked)
}

function onOpacity(event: Event) {
  emit("update:opacity", Number((event.target as HTMLInputElement).value))
}

function onRainCellsToggle(event: Event) {
  emit("update:rainCellsEnabled", (event.target as HTMLInputElement).checked)
}

function onNowcastingToggle(event: Event) {
  emit("update:nowcastingEnabled", (event.target as HTMLInputElement).checked)
}

function onTrafficToggle(event: Event) {
  emit("update:trafficEnabled", (event.target as HTMLInputElement).checked)
}

function onTrafficPredictionToggle(event: Event) {
  emit("update:trafficPredictionEnabled", (event.target as HTMLInputElement).checked)
}

function onSatelliteToggle(event: Event) {
  emit("update:satelliteEnabled", (event.target as HTMLInputElement).checked)
}

function onSatelliteOpacity(event: Event) {
  emit("update:satelliteOpacity", Number((event.target as HTMLInputElement).value))
}
</script>

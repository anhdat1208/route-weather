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
            <span>{{ legend.stops[legend.stops.length - 1]?.label ?? "Mạnh" }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RadarFrameResponse, RadarLegend } from "~/types/radar"

const props = defineProps<{
  enabled: boolean
  opacity: number
  loading: boolean
  errorMessage: string | null
  frame: RadarFrameResponse | null
  freshnessLabel: string | null
  timestampDisplay: string | null
}>()

const emit = defineEmits<{
  "update:enabled": [value: boolean]
  "update:opacity": [value: number]
  refresh: []
}>()

const legend = computed<RadarLegend | null>(() => props.frame?.legend ?? null)

const statusClass = computed(() => {
  if (props.frame?.status === "stale") return "text-amber-400"
  if (props.frame?.status === "ok") return "text-green-400"
  return "text-slate-400"
})

function onToggle(event: Event) {
  emit("update:enabled", (event.target as HTMLInputElement).checked)
}

function onOpacity(event: Event) {
  emit("update:opacity", Number((event.target as HTMLInputElement).value))
}
</script>

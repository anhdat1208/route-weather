<template>
  <div class="border-t border-slate-700/50 p-4">
    <h2 class="mb-3 text-sm font-semibold text-slate-200">Thời tiết trên lộ trình</h2>
    <div v-if="points.length" class="flex items-stretch gap-2 overflow-x-auto pb-2">
      <div
        v-for="point in points"
        :key="`tp-${point.index}`"
        class="min-w-[140px] rounded-xl border border-slate-700/50 bg-slate-900/40 px-3 py-2"
      >
        <div class="text-xs text-slate-400">{{ formatTime(point.arrival_time) }}</div>
        <div class="mt-1 text-sm font-medium">{{ point.label || "—" }}</div>
        <div class="mt-2 flex items-center justify-between">
          <span class="text-lg">{{ iconFor(point) }}</span>
          <span class="text-xs font-medium text-slate-200">
            {{ point.weather ? `${point.precipitation_probability_pct ?? 0}%` : "—" }}
          </span>
        </div>
        <div class="mt-2 text-xs text-slate-400">
          {{ point.weather?.temperature_c != null ? `${point.weather.temperature_c}°C` : "Thời tiết không khả dụng" }}
        </div>
        <div v-if="point.weather?.precipitation_mm != null" class="mt-1 text-[11px] text-slate-500">
          Lượng mưa: {{ point.weather.precipitation_mm }} mm
        </div>
      </div>
    </div>
    <div v-else class="text-sm text-slate-500">Chưa có timeline.</div>
  </div>
</template>

<script setup lang="ts">
import type { RouteWeatherTimelinePoint } from "~/types/routeWeather"

defineProps<{ points: RouteWeatherTimelinePoint[] }>()

function formatTime(v: string) {
  return new Date(v).toTimeString().slice(0, 5)
}

function iconFor(point: RouteWeatherTimelinePoint) {
  if (!point.weather) return "❓"
  const prob = point.precipitation_probability_pct ?? 0
  if (prob >= 80) return "🌧️"
  if (prob >= 60) return "🌦️"
  if (prob >= 40) return "🌥️"
  if (prob >= 20) return "🌤️"
  return "☀️"
}
</script>

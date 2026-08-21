<template>
  <div class="card space-y-2">
    <h2 class="text-sm font-semibold text-slate-300">Tổng quan hành trình</h2>
    <div class="grid grid-cols-2 gap-2 text-xs">
      <div>
        <span class="text-slate-400">Khoảng cách</span>
        <p class="font-medium">{{ distanceKm != null ? distanceKm.toFixed(1) : "—" }} km</p>
      </div>
      <div>
        <span class="text-slate-400">Thời gian di chuyển</span>
        <p class="font-medium">{{ durationMinutes != null ? Math.round(durationMinutes) : "—" }} phút</p>
      </div>
      <div>
        <span class="text-slate-400">Xuất phát</span>
        <p class="font-medium">{{ departureDisplay }}</p>
      </div>
      <div>
        <span class="text-slate-400">Đến nơi dự kiến</span>
        <p class="font-medium">{{ etaDisplay }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  distanceKm: number | null
  durationMinutes: number | null
  departureDisplay: string
  etaDisplay: string
}>()
</script>

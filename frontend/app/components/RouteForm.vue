<template>
  <div class="card space-y-3">
    <div class="relative">
      <label class="mb-1 block text-xs text-slate-400">Điểm đi</label>
      <input
        :value="originQuery"
        class="input-field"
        type="text"
        placeholder="Nhập địa chỉ xuất phát..."
        @input="$emit('update:originQuery', ($event.target as HTMLInputElement).value)"
      />
      <div v-if="originSuggestions.length" class="absolute z-20 mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 shadow-lg">
        <button
          v-for="item in originSuggestions"
          :key="`o-${item.label}-${item.point.lat}`"
          type="button"
          class="block w-full px-3 py-2 text-left text-xs text-slate-100 hover:bg-slate-800"
          @click="$emit('selectOrigin', item)"
        >
          {{ item.label }}
          <span v-if="item.approximate" class="ml-1 text-[10px] text-amber-300">(gần đúng theo tên đường)</span>
        </button>
      </div>
    </div>

    <div class="relative">
      <label class="mb-1 block text-xs text-slate-400">Điểm đến</label>
      <input
        :value="destinationQuery"
        class="input-field"
        type="text"
        placeholder="Nhập địa chỉ đích..."
        @input="$emit('update:destinationQuery', ($event.target as HTMLInputElement).value)"
      />
      <div v-if="destinationSuggestions.length" class="absolute z-20 mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 shadow-lg">
        <button
          v-for="item in destinationSuggestions"
          :key="`d-${item.label}-${item.point.lat}`"
          type="button"
          class="block w-full px-3 py-2 text-left text-xs text-slate-100 hover:bg-slate-800"
          @click="$emit('selectDestination', item)"
        >
          {{ item.label }}
          <span v-if="item.approximate" class="ml-1 text-[10px] text-amber-300">(gần đúng theo tên đường)</span>
        </button>
      </div>
    </div>

    <div>
      <label class="mb-1 block text-xs text-slate-400">Phương tiện</label>
      <select
        :value="travelMode"
        class="input-field"
        @change="$emit('update:travelMode', ($event.target as HTMLSelectElement).value)"
      >
        <option value="motorbike">Xe máy</option>
        <option value="walking">Đi bộ</option>
      </select>
    </div>

    <div>
      <label class="mb-1 block text-xs text-slate-400">Thời gian xuất phát</label>
      <input
        :value="departureLocal"
        class="input-field"
        type="datetime-local"
        @input="$emit('update:departureLocal', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <button class="btn-primary" type="button" :disabled="loading || !canSubmit" @click="$emit('analyze')">
      {{ loading ? loadingMessage || "Đang tính..." : "Phân tích lộ trình" }}
    </button>
    <p v-if="errorMessage" class="text-xs text-red-400">{{ errorMessage }}</p>
    <p v-if="weatherWarning" class="text-xs text-amber-300">{{ weatherWarning }}</p>
  </div>
</template>

<script setup lang="ts">
import type { GeocodeResult, TravelMode } from "~/types/routeWeather"

defineProps<{
  originQuery: string
  destinationQuery: string
  originSuggestions: GeocodeResult[]
  destinationSuggestions: GeocodeResult[]
  travelMode: TravelMode
  departureLocal: string
  loading: boolean
  loadingMessage: string
  errorMessage: string
  weatherWarning: string
  canSubmit: boolean
}>()

defineEmits<{
  "update:originQuery": [string]
  "update:destinationQuery": [string]
  "update:travelMode": [string]
  "update:departureLocal": [string]
  selectOrigin: [GeocodeResult]
  selectDestination: [GeocodeResult]
  analyze: []
}>()
</script>

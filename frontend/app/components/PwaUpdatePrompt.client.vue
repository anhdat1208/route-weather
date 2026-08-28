<template>
  <div
    v-if="pwa?.needRefresh || pwa?.offlineReady"
    class="fixed bottom-4 left-4 right-4 z-[99] mx-auto max-w-md rounded-xl border border-sky-600/40 bg-slate-900/95 p-4 shadow-xl backdrop-blur-sm md:left-auto md:right-4"
    role="status"
  >
    <p class="text-sm font-medium text-slate-100">
      {{ pwa?.needRefresh ? "Có phiên bản mới" : "Sẵn sàng dùng offline" }}
    </p>
    <p class="mt-1 text-xs text-slate-400">
      {{
        pwa?.needRefresh
          ? "Bấm cập nhật để tải bản mới nhất."
          : "Ứng dụng đã cache — dữ liệu thời tiết vẫn cần mạng."
      }}
    </p>
    <div class="mt-3 flex gap-2">
      <button
        v-if="pwa?.needRefresh"
        type="button"
        class="rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-500"
        @click="pwa?.updateServiceWorker(true)"
      >
        Cập nhật
      </button>
      <button
        type="button"
        class="rounded-lg px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
        @click="pwa?.closePrompt()"
      >
        Đóng
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const { $pwa } = useNuxtApp()
const pwa = $pwa as {
  needRefresh: boolean
  offlineReady: boolean
  updateServiceWorker: (reload?: boolean) => Promise<void>
  closePrompt: () => void
} | undefined
</script>

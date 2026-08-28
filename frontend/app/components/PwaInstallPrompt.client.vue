<template>
  <div
    v-if="pwa?.showInstallPrompt"
    class="fixed bottom-4 left-4 right-4 z-[100] mx-auto max-w-md rounded-xl border border-slate-600/60 bg-slate-900/95 p-4 shadow-xl backdrop-blur-sm md:left-auto md:right-4"
    role="dialog"
    aria-label="Cài đặt ứng dụng"
  >
    <div class="flex items-start gap-3">
      <img src="/icons/icon-192.png" alt="" class="h-12 w-12 shrink-0 rounded-xl" width="48" height="48" />
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold text-slate-100">Cài Route Weather</p>
        <p class="mt-1 text-xs text-slate-400">
          Thêm vào màn hình chính để mở nhanh như app — theo dõi thời tiết trên lộ trình.
        </p>
        <div class="mt-3 flex gap-2">
          <button
            type="button"
            class="rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-500"
            @click="pwa?.install()"
          >
            Cài app
          </button>
          <button
            type="button"
            class="rounded-lg px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
            @click="pwa?.cancelInstall()"
          >
            Để sau
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { $pwa } = useNuxtApp()
const pwa = $pwa as {
  showInstallPrompt: boolean
  install: () => Promise<void>
  cancelInstall: () => void
} | undefined
</script>

<template>
  <div class="min-h-screen">
    <NuxtRouteAnnouncer />
    <NuxtPage />
    <ClientOnly>
      <PwaInstallPrompt />
      <PwaUpdatePrompt />
    </ClientOnly>
  </div>
</template>

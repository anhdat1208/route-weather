// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    '@vite-pwa/nuxt',
  ],

  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
      mapStyleUrl: process.env.NUXT_PUBLIC_MAP_STYLE_URL || 'https://tiles.openfreemap.org/styles/liberty',
      enableFusionDebug: process.env.NUXT_PUBLIC_ENABLE_FUSION_DEBUG === 'true',
    },
  },

  pwa: {
    registerType: 'prompt',
    includeAssets: ['icons/*.png', 'robots.txt'],
    manifest: {
      name: 'Route Weather',
      short_name: 'RouteWeather',
      description: 'Biết thời tiết trên từng chặng đường',
      start_url: '/',
      display: 'standalone',
      orientation: 'portrait',
      theme_color: '#0f172a',
      background_color: '#0f172a',
      lang: 'vi',
      icons: [
        { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
        { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    workbox: {
      globPatterns: ['**/*.{js,css,html,png,ico,svg,woff2}'],
      navigateFallback: '/',
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/tiles\.openfreemap\.org\/.*/i,
          handler: 'CacheFirst',
          options: {
            cacheName: 'map-tiles',
            expiration: {
              maxEntries: 200,
              maxAgeSeconds: 60 * 60 * 24 * 7,
            },
          },
        },
      ],
    },
    client: {
      installPrompt: 'route-weather-install-dismissed',
      periodicSyncForUpdates: 3600,
    },
    devOptions: {
      enabled: true,
      type: 'module',
    },
  },

  app: {
    head: {
      title: 'Route Weather',
      meta: [
        { name: 'description', content: 'Biết thời tiết trên từng chặng đường' },
        { name: 'theme-color', content: '#0f172a' },
        { name: 'mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
      ],
      link: [{ rel: 'apple-touch-icon', href: '/icons/icon-192.png' }],
    },
  },
})

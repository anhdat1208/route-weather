const CACHE_NAME = 'route-weather-v1'
const STATIC_ASSETS = ['/', '/manifest.json', '/icons/icon-192.png', '/icons/icon-512.png']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  // Cache map tiles aggressively
  if (url.hostname === 'tiles.openfreemap.org') {
    event.respondWith(
      caches.open('map-tiles').then((cache) =>
        cache.match(event.request).then((cached) => {
          if (cached) return cached
          return fetch(event.request).then((resp) => {
            if (resp.ok) cache.put(event.request, resp.clone())
            return resp
          })
        })
      )
    )
    return
  }

  // Network-first for API calls
  if (url.pathname.startsWith('/api/')) return

  // Stale-while-revalidate for app shell
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request).then((resp) => {
        if (resp.ok) {
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resp.clone()))
        }
        return resp
      }).catch(() => cached)
      return cached || fetchPromise
    })
  )
})

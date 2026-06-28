const CACHE_NAME = 'eva-atem-app-v5';
const ASSETS_TO_CACHE = [
  './',
  './index.htm',
  './manifest.json',
  // Die externe Google Font ebenfalls cachen:
  'https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap'
];

// Installations-Event: Wird beim ersten Aufruf getriggert und speichert die Assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache erfolgreich geöffnet');
        return cache.addAll(ASSETS_TO_CACHE);
      })
  );
});

// Fetch-Event: Fängt Anfragen ab und liefert sie aus dem Cache
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Fall 1: Treffer im Cache gefunden -> direkt zurückgeben (Offline-Support)
        if (response) {
          return response;
        }
        // Fall 2: Nicht im Cache -> regulär aus dem Internet laden
        return fetch(event.request);
      })
  );
});

// Activate-Event: Räumt alte Caches auf (wichtig für spätere Updates)
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Nachricht vom Client (der App) empfangen, um den neuen SW sofort zu aktivieren
self.addEventListener('message', event => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
const CACHE_NAME = 'eva-atem-app-v6';
const ASSETS_TO_CACHE = [
  './',
  './index.htm',
  './manifest.json',
  'https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap'
];

// Installation: Cache befüllen + sofort aktivieren
self.addEventListener('install', event => {
  self.skipWaiting(); // Sofort aktivieren, nicht auf alte Tabs warten
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS_TO_CACHE))
  );
});

// Fetch: Network-First – immer zuerst frisch laden, Cache nur als Fallback
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Frische Antwort in Cache speichern
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      })
      .catch(() => {
        // Offline: Aus Cache laden
        return caches.match(event.request);
      })
  );
});

// Activate: Alle alten Caches löschen + sofort Kontrolle übernehmen
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(
        names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n))
      )
    ).then(() => self.clients.claim()) // Sofort alle Tabs übernehmen
  );
});

// Skip-Waiting Nachricht
self.addEventListener('message', event => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
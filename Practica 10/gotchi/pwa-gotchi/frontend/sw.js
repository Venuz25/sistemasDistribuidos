const CACHE_NAME = 'apigotchi-v1';
const urlsToCache = [
  './index.html',
  './style.css',
  './app.js',
  './manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  // Ignorar peticiones a la API para no guardarlas en caché estático
  if (event.request.url.includes('127.0.0.1')) {
      return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Devuelve la versión en caché si existe, si no, busca en la red
        return response || fetch(event.request);
      })
  );
});
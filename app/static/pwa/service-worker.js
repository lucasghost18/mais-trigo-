const CACHE_NAME = 'maistrigo-v1';
const OFFLINE_URL = '/';

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll([
      OFFLINE_URL,
    ]))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then(resp => {
      return resp || fetch(event.request).then(fetchResp => {
        return caches.open(CACHE_NAME).then(cache => {
          try { cache.put(event.request, fetchResp.clone()); } catch(e) {}
          return fetchResp;
        });
      }).catch(() => caches.match(OFFLINE_URL));
    })
  );
});

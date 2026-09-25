const CACHE='mgo-brain-v0511-shell';
const SHELL=['/','/manifest.webmanifest','/static/icon.svg','/static/i18n.js'];
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('mgo-brain-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', event => {
  const req=event.request;
  const url=new URL(req.url);
  if(req.method!=='GET' || url.origin !== self.location.origin) return;
  if(url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/') || url.pathname==='/health') return;
  const path=url.pathname;
  if(!SHELL.includes(path)) return;
  event.respondWith(fetch(req).then(res => {
    if(res.ok){const copy=res.clone();event.waitUntil(caches.open(CACHE).then(c=>c.put(path,copy)));}
    return res;
  }).catch(async()=> (await caches.match(path)) || Response.error()));
});

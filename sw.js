/*
 * Service worker of the portfolio app (installable on Android, iPhone and desktop).
 * Pages: network first, so a new version shows as soon as the phone is online; the last copy (or offline.html)
 * when it is not. Pictures, icons and fonts: cache first, refreshed in the background.
 * Only GET requests of this site and of Google Fonts are cached; everything else (GitHub badges, links) goes straight
 * to the network, so nothing private is stored.
 */
const VERSION = 'rbchy-app-v10';
const CORE = ['./', './index.html', './offline.html', './manifest.webmanifest', './app/icon-192.png', './app/icon-512.png',
  './og-card.png', './rbcimg.png', './shop-storefront.webp', './project-status.svg', './photo-bg.svg', './profile-card-bg.svg'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const sameSite = url => url.origin === self.location.origin && url.pathname.startsWith('/rbchy/');
const fonts = url => url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com';

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (!sameSite(url) && !fonts(url)) return;

  if (req.mode === 'navigate') {
    event.respondWith(fetch(req)
      .then(res => { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); return res; })
      .catch(async () => (await caches.match(req, { ignoreSearch: true }))
        || (await caches.match('./index.html')) || caches.match('./offline.html')));
    return;
  }

  event.respondWith(caches.match(req).then(hit => {
    const fresh = fetch(req).then(res => {
      if (res.ok || res.type === 'opaque') { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => hit);
    return hit || fresh;
  }));
});

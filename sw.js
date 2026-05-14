/* 天書奇談模擬器 — Service Worker (offline cache)
 * ⚠️ 發版時要同時改:
 *   1. 下面的 BUILD 字串(yyyy-mm-dd 格式)
 *   2. index.html footer 的版本字串(搜 "版本 v")
 * BUILD 變動 → CACHE 名稱跟著變 → 觸發 activate 階段刪舊 cache。
 */
const BUILD = '2026-05-12';            /* 發版日期,改這裡就好 */
const VERSION = 'v1.0';                /* semver,人看得懂的版本 */
const CACHE = `wondrous-tails-${VERSION}-${BUILD}`;
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.png',
  'https://cdn.tailwindcss.com',
  'https://unpkg.com/react@18/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
  'https://unpkg.com/@babel/standalone/babel.min.js'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c =>
      Promise.all(ASSETS.map(url =>
        c.add(url).catch(() => {/* 忽略單一資源失敗 */})
      ))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

/* Cache-first;只有「導航請求」失敗才回退到 index.html
 * (修正前的 bug:任何 JS/CSS 失敗也回 HTML,會導致瀏覽器把 HTML 當 JS 執行 → 整頁壞掉)
 */
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  e.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req).then(res => {
        if (res && res.status === 200 && (res.type === 'basic' || res.type === 'cors')) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(req, clone));
        }
        return res;
      }).catch(() => {
        // 只對 navigation request 回退到首頁,其他資源失敗就照實 reject
        if (req.mode === 'navigate') return caches.match('./index.html');
        return Response.error();
      });
    })
  );
});

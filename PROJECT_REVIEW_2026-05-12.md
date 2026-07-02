# 天書奇談模擬器 — 專案檢查報告

**日期：** 2026-05-12
**版本：** v1.0
**範圍：** 全專案 code review + PWA 體質檢查

---

## 🔴 嚴重 / 一定要處理

### 1. Service Worker 版本號是硬編碼,每次更新都要手動改

`sw.js` 第 2 行：
```js
const CACHE = 'wondrous-tails-v1.0';
```

PWA 用 cache-first 策略,使用者拿到的會永遠是第一次安裝的版本,**除非 CACHE 字串改變**。`activate` 階段才會刪掉名稱不同的舊 cache。這是 PWA 最常見的坑。

`index.html` footer 寫的「版本 v1.0」和這裡的 `v1.0` 是兩處獨立的字串,已經有同步風險。

### 2. 生產環境用瀏覽器內 Babel + Tailwind Play CDN

```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<script type="text/babel" data-presets="env,react">
```

`cdn.tailwindcss.com` 和 `@babel/standalone` 都是**明確只給開發環境使用**的,Tailwind Play CDN 還會在 console 顯示 warning。`babel.min.js` 約 3MB,且每次載入都要在使用者瀏覽器即時編譯整個 React app — 在低階手機上首屏可能要 2 ~ 3 秒。

### 3. `rank_tables.js` 是死檔案

`index.html` 第 206 行已經把 `RANK_TABLES` 整個 inline 進去了,但根目錄還有同名的 `rank_tables.js`,而且 `sw.js` 的 ASSETS 列表**也沒有引用它**。表示這個檔案完全沒被載入,但會跟 inline 版本**靜默 desync**。

而且把這麼大一坨 JSON 內嵌在 HTML,使得任何 UI 改動都會破壞 HTML 的快取,使用者要重下整包。

### 4. SW fallback 邏輯有 bug

`sw.js` 第 46 行：
```js
}).catch(() => caches.match('./index.html'));
```

任何 fetch 失敗（包括 React、Tailwind、Babel 那幾個外部 CDN）都會 fallback 到 `index.html`。**如果 React UMD 找不到,回傳 HTML 當作 JS 執行會直接整頁壞掉**。應該只對 navigation request (`req.mode === 'navigate'`) 做這個 fallback。

---

## 🟡 中等 / 建議處理

### 5. `gen_rank_table.py` 寫死了過期路徑

```python
out_path = "/sessions/inspiring-vigilant-knuth/mnt/outputs/rank_tables.js"
```

這是某次 Cowork 工作階段的臨時路徑,重跑會直接報錯。應改為 `os.path.join(os.path.dirname(__file__), "rank_tables.js")` 之類。

### 6. `STRATEGIES.gold` 物件的 key 用法不一致

```js
gold: { label: '金 = 3','desc': '正好 3 線機率',  metric: 'eq3' },
```

`'desc'` 用了字串引號,其他鍵沒有。同時 `metric` 字段在整個程式裡**完全沒被消費** — `metricValue()` 直接用 `if (strategy === ...)` 分支判斷,跟 `STRATEGIES[key].metric` 沒關係。要嘛刪掉 `metric` 欄位,要嘛改寫成資料驅動。

### 7. 重新貼按鈕不檢查 3 ~ 7 範圍

UI 上面寫著「印章 < 3 或 > 7 不可重新貼」,但 `reshuffle()` 只擋了 `count === 0`。使用者按下按鈕仍會「假裝重新貼成功」,跟遊戲內機制不符。

### 8. 沒有 `LICENSE` 檔

README 聲稱 MIT,但根目錄沒有 LICENSE 檔案 — GitHub 也偵測不到授權。

### 9. iOS safe-area 沒處理

雖然 `viewport-fit=cover` 設了,但 CSS 沒用 `env(safe-area-inset-*)`,iPhone 有瀏海／Dynamic Island 的機型,底部按鈕可能被 home indicator 蓋住。

### 10. Theme 沒讀 OS 偏好

```js
const [theme, setTheme] = useState(() => {
  try { return localStorage.getItem('wt-theme') || 'dark'; } catch { return 'dark'; }
});
```

預設一律深色 — 系統設淺色模式的使用者要手動切。建議在 fallback 用 `window.matchMedia('(prefers-color-scheme: light)')`。

---

## 🟢 細節

- `node_modules/` 雖然 `.gitignore` 已忽略,但放在 OneDrive 同步資料夾會吃同步流量。建議把專案放到非同步資料夾,或用 OneDrive 的「Files On-Demand」忽略此資料夾。
- `manifest.json` 兩個 icon 都指向同一張 `icon.png`,只是宣告 sizes 不同。實際 PWA install 在 Android 可能會用錯尺寸,建議準備真正的 192x192 和 512x512 兩張。
- README 標榜中英雙語但 UI 全是繁中。
- 沒有任何測試(JS 端)。Python 那邊有 print-based 驗證但不是 pytest assertions。

---

## 🔮 未來更新時的清單（踩坑備忘錄）

每次發版時請務必檢查：

1. **改 `sw.js` 的 `CACHE` 字串**（例如 `wondrous-tails-v1.1`），否則使用者拿不到新版本。
2. **同步改 `index.html` footer 的版本字串和日期**（目前在 line 724）。
3. **新增任何資源檔（圖片、JS、CSS）時,加進 `sw.js` 的 `ASSETS` 陣列**,否則離線時會抓不到。
4. **改 `RANK_TABLES` 資料**（例如修演算法後重跑 Python），記得**同時改 index.html 第 206 行的內嵌版本**（或乾脆改回引用獨立 .js 檔）。
5. **未來如果想拿掉 in-browser Babel/Tailwind CDN**（強烈建議）,SW 的 ASSETS 列表 + index.html 的 `<script>` 標籤 + 整個 build pipeline 都要動。是個獨立的小工程,可以列為 v2.0 的目標。
6. **重跑 `gen_rank_table.py` 前先改 `out_path`**。
7. **任何 localStorage key 命名要保持 `wt-` 前綴**,避免跟未來其他 PWA 衝突。

---

## 💡 最划算的快速修

如果只想用最少時間修最多坑,建議先做這四項（加起來大概十幾行修改）：

1. SW 版本號自動化（用 build time stamp 或 git commit hash）
2. 拿掉 dead 的 `rank_tables.js`
3. 修 SW fallback 的 navigation-only 邏輯
4. 修 Python 寫死路徑

# 📜 FF14 天書奇談模擬器 (Wondrous Tails Solver)

**FFXIV 庫洛日記 — 連線機率計算與「胡思亂想 · 重新貼」決策工具。**
**The Mobile-First, Offline-Capable Wondrous Tails Solver for FFXIV.**

👉 **立即使用:[點擊開啟模擬器](https://shu-xiao.github.io/wondrous-tails/)**

---

## 📖 專案簡介 (Introduction)

這是一個給《Final Fantasy XIV》光之戰士使用的 **天書奇談 (Wondrous Tails)** 輔助工具,專注解決一個關鍵決策:**什麼時候該用「胡思亂想 — 重新貼」?**

採用 **PWA (Progressive Web App)** 技術,專為手機體驗優化,開啟過一次後即可 **離線使用**,並能像原生 App 一樣加入桌面、全螢幕運行。

　

## ✨ 核心特色 (Features)

- **🧮 精確機率運算 (Exact Solver)**
  * 不是蒙地卡羅模擬,而是窮舉 **C(16-k, 9-k)** 全部排列計算精確分佈。
  * 已對照 FFXIV 社群公認的 9 印章隨機分佈 **41.54% / 47.90% / 10.35% / 0.21%** 完美驗證。
- **🎯 重新貼決策建議**
  * 即時計算當前期望線數 vs. 重新貼後期望線數。
  * 整合 Reddit 社群「7 印章決策法」,給出 **建議重新貼 / 不要重新貼 / 看心情** 三色提示。
- **⚡ PWA 離線支援**
  * 內建 Service Worker,加入主畫面後完全離線可用。
- **📱 手機友善 UI**
  * 4×4 大型觸控格,連線高亮顯示,點擊即時更新所有指標。
- **🔒 不蒐集任何資料**
  * 純前端,沒有後端、沒有追蹤、沒有 Cookie。

　

## 🛠️ 技術架構 (Tech Stack)

- **Core:** HTML5, CSS3, JavaScript (ES6+)
- **Framework:** React 18 (Via CDN, no build step required)
- **Styling:** Tailwind CSS (Via CDN)
- **PWA:** Service Worker + Web App Manifest

　

## 🎲 演算法說明

### 連線判定
4×4 棋盤共 **10 條線** = 4 橫 + 4 直 + 2 對角線。

### 期望分佈
給定當前 k 個印章位置,剩下的 (9-k) 個印章會在剩下的 (16-k) 個格子隨機分配,窮舉所有可能組合得到精確機率分佈。最大運算量 C(16,9) = 11,440 種組合,在現代瀏覽器毫秒內完成。

### 重新貼建議邏輯
- **印章 < 3** 或 **印章 > 7** → 不可使用
- **已有任何連線** → 不要重新貼 (重新貼後平均會變差)
- **0 連線 + 潛在 ≥ 3 線** → 絕對不要重新貼
- **0 連線 + 潛在 ≤ 1 線** → 強烈建議重新貼
- **0 連線 + 潛在 = 2 線** → 比較期望差值決定

　

## 📚 致謝與參考 (Credits & References)

本專案是非營利、開源的工具。核心策略與機率計算參考以下社群研究:

- [Wondrous Tails Analysis: When Should You Shuffle?](https://www.reddit.com/r/ffxiv/comments/550lo8/wondrous_tails_analysis_when_should_you_shuffle/) — Reddit 社群分析
- [Wondrous Tails Solver — Morpheusz](http://ffxiv.morpheusz.com/p/wondrous-tails-solver.html)
- [FF14 天書奇談計算器 — cycleapple](https://cycleapple.github.io/xiv-tc-wondrous-tails/) — UI 與決策表參考

　

## 📜 免責聲明 (Disclaimer)

- 本工具僅為前端機率計算輔助,不涉及任何遊戲封包修改或自動化操作,符合 FFXIV 使用規範。
- FINAL FANTASY is a registered trademark of Square Enix Holdings Co., Ltd.
- 本專案與 SQUARE ENIX 無任何關聯。

　

## 📝 授權 (License)

MIT License — 自由使用、修改、分發,但請保留原始致謝。

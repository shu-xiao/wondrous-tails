# 天書奇談模擬器 — 測試計畫

對一個純前端、核心是組合機率的工具,風險集中在**靜默的數值錯誤**:算錯一個機率或百分位不會丟例外、UI 照常顯示,只有結果偏掉。測試的重點因此放在「正確性護欄」,而非框架程式碼或 UI 細節。

## 測試金字塔(本專案實際比重)

```
        E2E / 視覺      —  暫不做(單人專案,成本 > 效益)
      整合(SW/PWA)    —  少量手動煙霧測試
   單元 / 屬性測試      —  主力,涵蓋全部數學核心
```

## 涵蓋範圍

### 1. Python — `test_rank_tables.py`(資料層)

驗證已提交的 `rank_tables.js` 正確無誤。手法是用**第二套完全獨立**的 brute-force 重新枚舉所有盤面,再與提交值逐 tier 比對 —— 兩套實作互為對照,任一邊算錯都會被抓出。

涵蓋:

- 逐 tier 分佈與獨立重算完全一致(k=0..9、ge1/ge2/ge3)
- `total == C(16,k)`、`denom == C(16-k, 9-k)`
- 每張表 count 總和 == total(機率質量守恆)
- numerator ∈ [0, denom]、count 為正
- tier 依 numerator 嚴格降序(前端「Tier 1 = 機率最高」仰賴此排序)
- 整體單調性:平均 P(≥1) ≥ P(≥2) ≥ P(≥3)
- 黃金值:k=7 的 P(≥3) = {3:16, 2:8, 1:800, 0:10616};k=9 全決定論

> 刻意**不** import `gen_rank_table.py`(它在 import 時即跑完計算並覆寫輸出檔),以確保是獨立的第二實作。

### 2. Node — `test_logic.mjs`(前端邏輯層)

測 `index.html` 內無 React 依賴的純函式。從原始檔抽出「棋盤定義 … 重骰勝率」之間那段直接 eval,**維持單一真實來源**,不複製副本。

涵蓋:

- `completedLines`:橫/直/斜判定、多線疊加、不足成線
- `expectedScore` / `cumulative`:加權與累積算術
- `expectedDistribution`:四格機率和為 1;k=0 等於 `RESHUFFLE_DIST`;k=9 決定論落點
- **屬性測試**(400 局隨機盤面 × 3 目標,約 1200 次呼叫)針對 PR 百分位功能的關鍵不變量:
  - 真實盤面的 `userNumer` 經 `Math.round` 後**必命中**某個 tier(`tierIdx ≥ 0`)—— 直接堵住程式碼註解擔心的浮點/捨入邊界
  - 分割守恆:`strictlyWorse + strictlyBetter + tierCount == total`
  - 百分位界限:`strictlyWorse / total ∈ [0, 1)`
- 退化盤面判定(k=0 單 tier → 顯示「—」;k=9 非退化)

## 執行

```bash
python3 tests/test_rank_tables.py    # 約 5 秒
node    tests/test_logic.mjs          # 約 1 秒
```

兩者皆零外部依賴、退出碼非 0 即失敗,可直接接 CI 或 git pre-commit hook。

## 已知缺口 / 未涵蓋(建議排序)

1. **Service Worker 快取生命週期** — `BUILD`/`VERSION`/footer 三處版本字串同步、舊 cache 清除,目前靠人工。可加一個小腳本檢查三處字串一致(過去踩過版本不同步的坑)。
2. **`reshuffleWinRate` / `reshuffleAdvice`** — 重骰建議邏輯(含 balanced 策略的 on-the-fly bitmask 計算)尚未測;可比照屬性測試補不變量。
3. **React 元件 / 互動** — 點貼紙、目標切換、面板開合等 UI 行為無自動化測試。單人專案下優先度最低。
4. **`expectedRankInfo` 百分位索引** — 眾數/中位/分位點的 index 計算僅間接覆蓋,可補黃金值。

## 維護注意

- `test_logic.mjs` 靠兩個註解標記定位抽取區塊;若改動 `index.html` 那兩行註解,需同步更新標記(測試會明確報「找不到標記」)。
- 版控寫操作(`git add` 等)請在 Windows 端做,勿在沙盒 mount 內執行。

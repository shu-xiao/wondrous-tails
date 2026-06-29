/*
 * 測試 index.html 內的純數學函式(無 React 依賴的核心邏輯)。
 *
 * 作法:直接從 index.html 抽出「棋盤/連線定義 … 重骰勝率」之間那段純函式
 * 原始碼來 eval,維持單一真實來源 —— 不複製一份會走樣的副本。
 * 這段區塊不含任何 JSX 或 React hook,故可在純 Node 環境執行。
 *
 * 執行:  node tests/test_logic.mjs
 * 依賴:  僅 Node 內建(fs / path / url)
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const html = readFileSync(join(ROOT, "index.html"), "utf8");

// 抽出兩個註解標記之間的純函式區塊(含 RANK_TABLES)
const START = "/* ────────── 棋盤 / 連線定義 ────────── */";
const END = "/* ────────── 重骰勝率 ──────────";
const startIdx = html.indexOf(START);
const endIdx = html.indexOf(END);
if (startIdx < 0 || endIdx < 0 || endIdx <= startIdx) {
  console.error("❌ 找不到純函式區塊標記(index.html 結構可能變了,請更新標記)");
  process.exit(1);
}
const block = html.slice(startIdx, endIdx);

// 在隔離作用域 eval,把要測的符號 return 出來
const exported = new Function(`
  ${block}
  return { LINES, completedLines, countLinesMask, expectedScoreMask,
           combinations, expectedDistribution, potentialLines,
           RESHUFFLE_DIST, expectedScore, cumulative, RANK_TABLES,
           rankInfo, expectedRankInfo };
`)();

const {
  LINES, completedLines, expectedDistribution, expectedScore,
  cumulative, RANK_TABLES, rankInfo, RESHUFFLE_DIST, potentialLines,
} = exported;

// ─── 迷你斷言框架 ───
let checks = 0;
const fails = [];
function check(cond, msg) {
  checks++;
  if (!cond) fails.push(msg);
}
function near(a, b, eps = 1e-9) {
  return Math.abs(a - b) <= eps;
}
const setOf = (...idx) => new Set(idx);

// ─── 1. 連線定義 ───
check(LINES.length === 10, "LINES 應有 10 條(4 橫 + 4 直 + 2 斜)");
// 一條完整橫列 → 1 線
check(completedLines(setOf(0, 1, 2, 3)).length === 1, "整列應算 1 線");
// 主對角
check(completedLines(setOf(0, 5, 10, 15)).length === 1, "主對角應算 1 線");
// 同時湊滿一橫一直(共用一格,7 格)→ 2 線
check(completedLines(setOf(0, 1, 2, 3, 4, 8, 12)).length === 2, "一橫一直應算 2 線");
// 不足一線
check(completedLines(setOf(0, 1, 2)).length === 0, "三格不成線");

// ─── 2. expectedScore / cumulative 純算術 ───
const d = { 0: 0.1, 1: 0.2, 2: 0.3, 3: 0.4 };
check(near(expectedScore(d), 0.2 + 0.6 + 1.2), "expectedScore 加權和錯誤");
const cum = cumulative(d);
check(near(cum.ge1, 0.9) && near(cum.ge2, 0.7) && near(cum.eq3, 0.4), "cumulative 累積錯誤");

// ─── 3. expectedDistribution ───
// 空盤(k=0):應等於 RESHUFFLE_DIST(填 9/16 的基準分佈)
const e0 = expectedDistribution(new Set());
check(e0.total === 11440, `k=0 total 應為 11440,得 ${e0.total}`);
for (const k of [0, 1, 2, 3]) {
  check(near(e0.dist[k], RESHUFFLE_DIST[k]), `k=0 dist[${k}] 不等於 RESHUFFLE_DIST`);
}
// 任意盤面:四格機率和為 1
function distSumsToOne(stamped) {
  const { dist } = expectedDistribution(stamped);
  return near(dist[0] + dist[1] + dist[2] + dist[3], 1);
}
check(distSumsToOne(setOf(0, 5)), "k=2 dist 總和應為 1");
check(distSumsToOne(setOf(0, 1, 2, 3, 8, 12)), "k=6 dist 總和應為 1");
// 滿盤(k=9)決定論:湊好一橫一直(7 格)再補 2 格非線位 → 落點 dist[2]=1
const full9 = setOf(0, 1, 2, 3, 4, 8, 12, 9, 14); // 第一列 + 第一行 + 兩個不成線的雜格
const e9 = expectedDistribution(full9);
check(e9.total === 1, "k=9 應決定論 total=1");
check(e9.dist[2] === 1, `k=9 已湊 2 線,dist[2] 應為 1,得 ${JSON.stringify(e9.dist)}`);

// potentialLines:同盤面最佳情況 >= 目前線數
check(potentialLines(setOf(0, 1, 2)) >= 1, "三格的潛在連線應 >=1(可補成一列)");

// ─── 4. 屬性測試:rankInfo 的 numerator 必落在真實 tier 上 ───
// 這正是 PR 百分位功能仰賴的不變量(round() 後須命中,否則 tierIdx=-1)。
function randomBoard(k) {
  const cells = [...Array(16).keys()];
  for (let i = cells.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [cells[i], cells[j]] = [cells[j], cells[i]];
  }
  return new Set(cells.slice(0, k));
}
let propRuns = 0;
for (let trial = 0; trial < 400; trial++) {
  const k = 1 + Math.floor(Math.random() * 8); // k = 1..8
  const board = randomBoard(k);
  const { dist } = expectedDistribution(board);
  for (const goal of ["ge1", "ge2", "ge3"]) {
    const ri = rankInfo(k, dist, goal);
    if (!ri) continue;
    propRuns++;
    // (a) 真實盤面的 numerator 必須命中某個 tier(否則百分位/ tier 會顯示 —)
    check(ri.tierIdx >= 0,
      `k=${k} ${goal}: userNumer ${ri.userNumer} 未命中任何 tier (round/FP 問題)`);
    // (b) 分割守恆:strictlyWorse + strictlyBetter + 本 tier count == total
    if (ri.tierIdx >= 0) {
      check(ri.strictlyWorse + ri.strictlyBetter + ri.tierCount === ri.total,
        `k=${k} ${goal}: 分割不守恆 (${ri.strictlyWorse}+${ri.strictlyBetter}+${ri.tierCount} != ${ri.total})`);
    }
    // (c) 百分位界限:0 <= strictlyWorse/total < 1
    const pr = ri.strictlyWorse / ri.total;
    check(pr >= 0 && pr < 1, `k=${k} ${goal}: PR 百分位 ${pr} 超出 [0,1)`);
  }
}
check(propRuns > 500, `屬性測試樣本太少 (${propRuns})`);

// ─── 5. 退化盤面(PR 功能據此顯示「—」)───
check(RANK_TABLES["0"].ge1.length === 1, "k=0 ge1 應為單一 tier(退化)");
check(RANK_TABLES["9"].ge3.length === 2, "k=9 ge3 應有 2 個 tier(非退化)");

// ─── 結果 ───
console.log(`檢查項目: ${checks}(含屬性測試 ${propRuns} 次 rankInfo 呼叫)`);
if (fails.length) {
  console.error(`\n❌ 失敗 ${fails.length} 項:`);
  for (const f of fails) console.error("  -", f);
  process.exit(1);
}
console.log("✅ 全部通過 — index.html 純邏輯函式行為正確");

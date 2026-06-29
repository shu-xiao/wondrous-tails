"""
獨立重算 + 交叉驗證 RANK_TABLES(天書全局排名表)。

策略:本檔用「完全獨立」的第二套 brute-force 實作重新枚舉所有盤面,
再跟已提交的 rank_tables.js 逐 tier 比對。任何一邊算錯都會被抓到。
故意「不」import gen_rank_table.py —— 它在 import 時就會跑完整計算並覆寫
rank_tables.js,且我們要的是獨立的第二實作,而非沿用同一份程式。

執行:  python3 tests/test_rank_tables.py
依賴:  僅標準函式庫
"""
import json
import os
import re
import sys
from collections import Counter
from itertools import combinations
from math import comb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── 連線遮罩(獨立重寫,不沿用 gen_rank_table) ───
LINES_MASK = []
for r in range(4):
    LINES_MASK.append(sum(1 << (r * 4 + c) for c in range(4)))   # 橫列
for c in range(4):
    LINES_MASK.append(sum(1 << (r * 4 + c) for r in range(4)))   # 直行
LINES_MASK.append(sum(1 << i for i in (0, 5, 10, 15)))           # 主對角
LINES_MASK.append(sum(1 << i for i in (3, 6, 9, 12)))            # 副對角


def count_lines(bitmask):
    return sum(1 for lm in LINES_MASK if (bitmask & lm) == lm)


def derive_table(k):
    """回傳 {'total', 'denom', 'ge1','ge2','ge3'},tier dict 為 {numerator: count}。"""
    need = 9 - k
    denom = 1 if need == 0 else comb(16 - k, need)
    ge = {1: Counter(), 2: Counter(), 3: Counter()}
    total = 0
    cells = range(16)
    for placed in combinations(cells, k):
        bm = 0
        for c in placed:
            bm |= 1 << c
        empty = [c for c in cells if not (bm >> c) & 1]
        line_dist = Counter()
        if need == 0:
            line_dist[count_lines(bm)] = 1
        else:
            for combo in combinations(empty, need):
                full = bm
                for c in combo:
                    full |= 1 << c
                line_dist[count_lines(full)] += 1
        for tgt in (1, 2, 3):
            num = sum(c for nl, c in line_dist.items() if nl >= tgt)
            ge[tgt][num] += 1
        total += 1
    return {
        "total": total,
        "denom": denom,
        "ge1": dict(ge[1]),
        "ge2": dict(ge[2]),
        "ge3": dict(ge[3]),
    }


def load_committed():
    """從 rank_tables.js 取出 RANK_TABLES 物件。"""
    path = os.path.join(ROOT, "rank_tables.js")
    with open(path, encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"const RANK_TABLES\s*=\s*(\{.*\});", src, re.S)
    if not m:
        raise AssertionError("rank_tables.js 找不到 RANK_TABLES 物件")
    return json.loads(m.group(1))


def tiers_to_dict(tier_list):
    """[{'n':..,'c':..}, ...] → {n: c},順帶檢查 n 不重複。"""
    d = {}
    for t in tier_list:
        assert t["n"] not in d, f"重複的 numerator {t['n']}"
        d[t["n"]] = t["c"]
    return d


# ─── 測試 ───
FAILS = []
CHECKS = 0


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)


def main():
    committed = load_committed()

    for k in range(0, 10):
        ck = committed[str(k)]
        ref = derive_table(k)

        # 1) total == C(16,k);denom == C(16-k,9-k)
        check(ck["total"] == comb(16, k), f"k={k}: total {ck['total']} != C(16,{k})={comb(16,k)}")
        check(ck["total"] == ref["total"], f"k={k}: total 與獨立重算不符")
        check(ck["denom"] == ref["denom"], f"k={k}: denom {ck['denom']} != 期望 {ref['denom']}")

        for goal in ("ge1", "ge2", "ge3"):
            tiers = ck[goal]
            tier_d = tiers_to_dict(tiers)

            # 2) 逐 tier 與獨立重算完全相同
            check(tier_d == ref[goal], f"k={k} {goal}: tier 分佈與獨立重算不符")

            # 3) 每張表的 count 總和 == total
            csum = sum(t["c"] for t in tiers)
            check(csum == ck["total"], f"k={k} {goal}: count 總和 {csum} != total {ck['total']}")

            # 4) numerator 落在 [0, denom];count 為正
            for t in tiers:
                check(0 <= t["n"] <= ck["denom"], f"k={k} {goal}: numerator {t['n']} 超出 [0,{ck['denom']}]")
                check(t["c"] > 0, f"k={k} {goal}: 非正 count {t['c']}")

            # 5) tier 依 numerator 嚴格遞減(前端 Tier 1 = 機率最高 仰賴此排序)
            ns = [t["n"] for t in tiers]
            check(ns == sorted(ns, reverse=True), f"k={k} {goal}: 未依 numerator 降序排列")
            check(len(ns) == len(set(ns)), f"k={k} {goal}: numerator 有重複")

        # 6) 同盤面單調性:P(≥1) >= P(≥2) >= P(≥3) 的總期望
        #    用加權平均 numerator/denom 比較(整體層級的 sanity check)
        def mean_prob(goal):
            tot = sum(t["c"] for t in ck[goal])
            return sum(t["n"] * t["c"] for t in ck[goal]) / (ck["denom"] * tot)
        check(mean_prob("ge1") >= mean_prob("ge2") >= mean_prob("ge3") - 1e-12,
              f"k={k}: 平均機率未滿足 ge1>=ge2>=ge3")

    # 7) 黃金值:k=7 的 P(≥3) 分佈(gen_rank_table.py 內建斷言的同一組)
    g7 = tiers_to_dict(committed["7"]["ge3"])
    check(g7 == {3: 16, 2: 8, 1: 800, 0: 10616}, f"k=7 ge3 黃金值不符: {g7}")

    # 8) k=9 全決定論:denom=1,P(≥1) 命中數 6688(= 含至少一線的 9 子盤面數)
    check(committed["9"]["denom"] == 1, "k=9 denom 應為 1")
    g9_ge1 = tiers_to_dict(committed["9"]["ge1"])
    check(g9_ge1.get(1) == 6688 and g9_ge1.get(0) == 4752, f"k=9 ge1 黃金值不符: {g9_ge1}")

    print(f"檢查項目: {CHECKS}")
    if FAILS:
        print(f"\n❌ 失敗 {len(FAILS)} 項:")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("✅ 全部通過 — 已提交的 rank_tables.js 與獨立重算逐 tier 一致")


if __name__ == "__main__":
    main()

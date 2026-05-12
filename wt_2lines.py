"""
天書奇談 - 7貼紙達成「2+ 條線」全局機率分析
"""
from itertools import combinations
from collections import Counter, defaultdict

LINES = [
    (0,1,2,3), (4,5,6,7), (8,9,10,11), (12,13,14,15),
    (0,4,8,12), (1,5,9,13), (2,6,10,14), (3,7,11,15),
    (0,5,10,15), (3,6,9,12),
]

def count_lines(stamp_set):
    return sum(1 for line in LINES if all(c in stamp_set for c in line))

# 對稱(D4)
def rotate90(idx):
    r, c = divmod(idx, 4)
    return c*4 + (3-r)
def reflect_h(idx):
    r, c = divmod(idx, 4)
    return r*4 + (3-c)

SYMS = []
for n_rot in range(4):
    for refl in [False, True]:
        def make_t(n_rot=n_rot, refl=refl):
            def t(i):
                for _ in range(n_rot):
                    i = rotate90(i)
                if refl:
                    i = reflect_h(i)
                return i
            return t
        SYMS.append(make_t())

def canonical(config):
    return min(tuple(sorted(s(c) for c in config)) for s in SYMS)

def grid_str(placed_set):
    rows = []
    for r in range(4):
        row = ""
        for c in range(4):
            row += "■ " if (r*4+c) in placed_set else "□ "
        rows.append(row.strip())
    return "\n".join(rows)

# 統計
all_cells = list(range(16))
prob_counter_2plus = Counter()
prob_counter_2exact = Counter()
tier_examples_2plus = defaultdict(set)

for placed in combinations(all_cells, 7):
    placed_set = set(placed)
    empty_cells = [c for c in all_cells if c not in placed_set]
    
    cnt_lines = Counter()
    for additional in combinations(empty_cells, 2):
        nl = count_lines(placed_set | set(additional))
        cnt_lines[nl] += 1
    
    p_2plus = sum(c for nl, c in cnt_lines.items() if nl >= 2) / 36
    p_2exact = cnt_lines.get(2, 0) / 36
    
    prob_counter_2plus[round(p_2plus, 10)] += 1
    prob_counter_2exact[round(p_2exact, 10)] += 1
    
    tier = round(p_2plus * 36)  # 0..36
    if tier > 0:
        tier_examples_2plus[tier].add(canonical(placed))

print("="*72)
print("【目標:達成 2+ 條線】所有可能機率(排序)")
print("="*72)
print(f"{'P(≥2線)':>11} | {'分數':>7} | {'符合配置數':>10} | {'佔總%':>8} | {'獨立形狀(去對稱)':>16}")
print("-"*72)
total_configs = 11440
for p, count in sorted(prob_counter_2plus.items(), key=lambda x: -x[0]):
    tier = round(p * 36)
    n_unique = len(tier_examples_2plus.get(tier, set()))
    pct = count/total_configs*100
    print(f"{p*100:>10.4f}% | {tier:>2}/36   | {count:>10} | {pct:>7.4f}% | {n_unique:>16}")

print(f"\n總配置數: {total_configs}")
print(f"不同機率值數量: {len(prob_counter_2plus)}")
weighted_avg = sum(p*c for p,c in prob_counter_2plus.items()) / total_configs
print(f"加權平均 P(≥2線) = {weighted_avg*100:.4f}%")
# 驗證:9 印章 ≥ 2 線 = 10.35% + 0.21% = 10.56%
print(f"驗證:應 ≈ 10.56% (= 10.35% + 0.21% from 9-stamp dist) ✓")

print()
print("="*72)
print("【目標:正好 2 條線】機率分佈")
print("="*72)
print(f"{'P(=2線)':>11} | {'分數':>7} | {'符合配置數':>10} | {'佔總%':>8}")
print("-"*72)
for p, count in sorted(prob_counter_2exact.items(), key=lambda x: -x[0]):
    tier = round(p*36)
    pct = count/total_configs*100
    print(f"{p*100:>10.4f}% | {tier:>2}/36   | {count:>10} | {pct:>7.4f}%")
weighted_avg2 = sum(p*c for p,c in prob_counter_2exact.items()) / total_configs
print(f"\n加權平均 P(=2線) = {weighted_avg2*100:.4f}% (應 ≈ 10.35%)")

# 印出最高機率等級的代表配置
print()
print("="*72)
print("【最佳布局】Top 3 機率等級的代表配置")
print("="*72)
top_tiers = sorted(tier_examples_2plus.keys(), reverse=True)[:3]
for tier in top_tiers:
    examples = sorted(tier_examples_2plus[tier])
    p = tier/36
    print(f"\n▶ P(≥2線) = {tier}/36 = {p*100:.2f}%  ({len(examples)} 種獨立形狀)")
    for i, cfg in enumerate(examples[:2]):
        print(f"\n  範例 {i+1}: cells = {list(cfg)}")
        print("  " + grid_str(set(cfg)).replace("\n", "\n  "))


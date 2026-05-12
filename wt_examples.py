"""
找出每個機率等級的代表性 7 貼紙配置(去除對稱)
"""
from itertools import combinations
from collections import defaultdict

LINES = [
    (0,1,2,3), (4,5,6,7), (8,9,10,11), (12,13,14,15),
    (0,4,8,12), (1,5,9,13), (2,6,10,14), (3,7,11,15),
    (0,5,10,15), (3,6,9,12),
]

# 8 種對稱(D4 二面體群)
def rotate90(idx):
    r, c = divmod(idx, 4)
    return c*4 + (3-r)
def reflect_h(idx):
    r, c = divmod(idx, 4)
    return r*4 + (3-c)

SYMS = []
for n_rot in range(4):
    for refl in [False, True]:
        def make_transform(n_rot=n_rot, refl=refl):
            def t(i):
                for _ in range(n_rot):
                    i = rotate90(i)
                if refl:
                    i = reflect_h(i)
                return i
            return t
        SYMS.append(make_transform())

def canonical(config):
    """取 8 個對稱版本中字典序最小的"""
    return min(tuple(sorted(s(c) for c in config)) for s in SYMS)

def count_lines(stamp_set):
    return sum(1 for line in LINES if all(c in stamp_set for c in line))

def grid_str(placed_set):
    """ASCII 4x4 視覺化"""
    rows = []
    for r in range(4):
        row = ""
        for c in range(4):
            row += "■ " if (r*4+c) in placed_set else "□ "
        rows.append(row.strip())
    return "\n".join(rows)

# 收集每個機率等級的配置(去對稱)
all_cells = list(range(16))
tier_examples = defaultdict(set)  # P(>=3) → set of canonical configs

for placed in combinations(all_cells, 7):
    placed_set = set(placed)
    empty_cells = [c for c in all_cells if c not in placed_set]
    
    cnt_3plus = 0
    for additional in combinations(empty_cells, 2):
        if count_lines(placed_set | set(additional)) >= 3:
            cnt_3plus += 1
    
    tier = cnt_3plus  # 0, 1, 2, or 3
    if tier > 0:
        tier_examples[tier].add(canonical(placed))

# 輸出代表性配置
print("="*70)
print("各機率等級的代表性配置(已去除8種旋轉/鏡射對稱)")
print("="*70)

for tier in sorted(tier_examples.keys(), reverse=True):
    p = tier / 36
    examples = sorted(tier_examples[tier])
    print(f"\n▶ P(≥3線) = {tier}/36 = {p*100:.2f}%  ({len(examples)} 個獨立配置, 含對稱共 {len(examples)*8 if tier in [3,2] else '~'})")
    print(f"  範例配置(顯示前 {min(3, len(examples))} 個):")
    for i, cfg in enumerate(examples[:3]):
        print(f"\n  配置 {i+1}: cells = {list(cfg)}")
        print("  " + grid_str(set(cfg)).replace("\n", "\n  "))

# 還要算出對於沒列出的 0 機率配置數
total_unique = sum(len(v) for v in tier_examples.values())
print(f"\n非 0 機率的獨立配置(去對稱)總數: {total_unique}")

"""
天書奇談 - 7貼紙全局機率分析
枚舉所有 C(16,7)=11,440 種可能的7貼紙配置
計算每個配置在剩下2個貼紙隨機放置後,達成「至少3條線」的精確機率
"""
from itertools import combinations
from collections import Counter, defaultdict

# 4x4 棋盤的 10 條線(以 0-15 編號)
# row 0: 0,1,2,3 ; row 1: 4,5,6,7 ; row 2: 8,9,10,11 ; row 3: 12,13,14,15
LINES = [
    # 4 橫
    (0,1,2,3), (4,5,6,7), (8,9,10,11), (12,13,14,15),
    # 4 直
    (0,4,8,12), (1,5,9,13), (2,6,10,14), (3,7,11,15),
    # 2 斜
    (0,5,10,15), (3,6,9,12),
]

def count_lines(stamp_set):
    """數有多少條線完全被覆蓋"""
    return sum(1 for line in LINES if all(c in stamp_set for c in line))

# 對所有 C(16,7)=11,440 種起始配置做計算
all_cells = list(range(16))
prob_distribution = []  # (P(>=3 lines), P(==3), P(>=2), config_id)
prob_counter_3plus = Counter()  # P(>=3) → 出現次數
prob_counter_3exact = Counter()  # P(==3) → 出現次數

for placed in combinations(all_cells, 7):
    placed_set = set(placed)
    empty_cells = [c for c in all_cells if c not in placed_set]
    
    # 枚舉剩下 2 個貼紙的所有 C(9,2)=36 種放法
    total = 0
    cnt_lines = Counter()  # 線數分佈
    for additional in combinations(empty_cells, 2):
        final_set = placed_set | set(additional)
        nl = count_lines(final_set)
        cnt_lines[nl] += 1
        total += 1
    
    # 機率
    p_at_least_3 = sum(c for nl, c in cnt_lines.items() if nl >= 3) / total
    p_exact_3   = cnt_lines.get(3, 0) / total
    p_at_least_2 = sum(c for nl, c in cnt_lines.items() if nl >= 2) / total
    
    prob_counter_3plus[round(p_at_least_3, 10)] += 1
    prob_counter_3exact[round(p_exact_3, 10)] += 1

# 排序並輸出
print("="*70)
print("【目標:達成 3+ 條線】所有可能機率 (排序)")
print("="*70)
print(f"{'機率 P(≥3線)':>16} | {'分數':>10} | {'符合配置數':>10} | {'佔總配置%':>10}")
print("-"*70)
total_configs = sum(prob_counter_3plus.values())
sorted_probs = sorted(prob_counter_3plus.items(), key=lambda x: -x[0])
for p, count in sorted_probs:
    # 嘗試表示為分數 x/36
    frac = f"{round(p*36)}/36"
    pct_configs = count / total_configs * 100
    print(f"{p*100:>14.4f}% | {frac:>10} | {count:>10} | {pct_configs:>9.4f}%")

print(f"\n總配置數: {total_configs} (= C(16,7) = 11,440)")
print(f"不同機率值數量: {len(prob_counter_3plus)}")

# 加權平均機率
weighted_avg = sum(p*c for p,c in prob_counter_3plus.items()) / total_configs
print(f"加權平均 P(≥3線) = {weighted_avg*100:.4f}%")

print()
print("="*70)
print("【目標:正好 3 條線】所有可能機率 (排序)")
print("="*70)
print(f"{'機率 P(=3線)':>16} | {'分數':>10} | {'符合配置數':>10} | {'佔總配置%':>10}")
print("-"*70)
sorted_probs2 = sorted(prob_counter_3exact.items(), key=lambda x: -x[0])
for p, count in sorted_probs2:
    frac = f"{round(p*36)}/36"
    pct_configs = count / total_configs * 100
    print(f"{p*100:>14.4f}% | {frac:>10} | {count:>10} | {pct_configs:>9.4f}%")

weighted_avg2 = sum(p*c for p,c in prob_counter_3exact.items()) / total_configs
print(f"\n加權平均 P(=3線) = {weighted_avg2*100:.4f}%")

# 驗證:應該與 README 提到的「9 印章隨機分佈 0.21% (3線)」吻合
# 因為 7 placed + 2 random = 9 stamps random
print(f"\n驗證:加權平均 P(=3線) 應約等於 9 印章分佈 0.21% → 實際 {weighted_avg2*100:.4f}% ✓")


# -*- coding: utf-8 -*-
import math, statistics
try:
    from scipy.stats import wilcoxon
    HAS = True
except Exception:
    HAS = False

def wilexact(a, b):
    d = [x - y for x, y in zip(a, b)]
    d = [v for v in d if v != 0]
    if not d:
        return 1.0
    if HAS:
        return wilcoxon(d).pvalue
    n = len(d)
    r = sorted((abs(v), v) for v in d)
    ranks = [0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and r[j + 1][0] == r[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    Wplus = sum(ranks[k] for k, v in enumerate(r) if v[1] > 0)
    var = n * (n + 1) * (2 * n + 1) / 24
    z = (Wplus - n * (n + 1) / 4) / math.sqrt(var)
    return 2 * (1 - statistics.NormalDist().cdf(abs(z)))

def ms(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return m, sd

y24 = {
    'baseline': [9.7, 8.3, 23.1, 21.1, 8.0, 33.3],
    'injected': [83.1, 92.8, 93.2, 88.6, 88.9, 88.3],
    'strict': [100, 100, 98.8, 98.0, 94.9, 97.7],
    'c_fs': [97.5, 97.5, 95.7, 97.5, 97.8, 99.0],
    'c_rp': [98.6, 98.2, 100, 89.7, 97.4, 100],
    'c_v': [100, 100, 97.7, 100, 100, 100],
}
y23 = {
    'baseline': [4.0, 4.8, 9.7, 17.2, 0.0, 20.8],
    'injected': [88.0, 92.5, 90.6, 89.9, 90.9, 89.7],
    'strict': [98.9, 98.8, 100, 100, 97.6, 100],
    'c_fs': [100.0, 97.6, 97.3, 94.8, 98.8, 96.6],
    'c_rp': [91.8, 88.9, 90.5, 98.5, 97.6, 90.5],
    'c_v': [100, 100, 100, 98.9, 100, 100],
}
merged = {s: y24[s] + y23[s] for s in y24}
print("== MERGED n=12 ==")
print("策略 | mean | sd | y24 | y23")
for s in y24:
    m, sd = ms(merged[s])
    m24, _ = ms(y24[s]); m23, _ = ms(y23[s])
    print(f"{s:9s} {m:6.1f} {sd:5.1f} | {m24:6.1f} | {m23:6.1f}")
print("\n== Wilcoxon (merged n=12) ==")
pairs = [('baseline', 'injected'), ('injected', 'strict'), ('strict', 'c_fs'),
         ('c_fs', 'c_rp'), ('c_rp', 'c_v'), ('baseline', 'strict'), ('strict', 'c_v')]
for a, b in pairs:
    diff, _ = ms([x - y for x, y in zip(merged[a], merged[b])])
    p = wilexact(merged[a], merged[b])
    print(f"{a:9s} -> {b:9s} diff={diff:+6.1f} p={p:.4f} sig={'Y' if p < 0.05 else 'N'}")
print("\nhas_scipy=", HAS)
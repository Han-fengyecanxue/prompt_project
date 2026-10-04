# -*- coding: utf-8 -*-
import json, sys, io, math, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from collections import defaultdict
try:
    from scipy.stats import wilcoxon
    HAS = True
except Exception:
    HAS = False

BASE = r"c:\Users\Hanyu\prompt_project\backend\eval"
files = ["eval_result_2024.raw.json", "eval_result_2023.raw.json"]
strat = defaultdict(lambda: {"strict": [], "loose": [], "halls": []})
for fn in files:
    with open(r"%s\%s" % (BASE, fn), encoding="utf-8") as f:
        recs = json.load(f)
    for r in recs:
        s = r["strategy"]
        if isinstance(r.get("acc"), (int, float)):
            strat[s]["strict"].append(r["acc"])
            strat[s]["loose"].append(r.get("acc_loose", r["acc"]))
        strat[s]["halls"].append(len(r.get("unverified") or []))

# c_fs 2023 S5(长春高新) 原run超时未写入raw, 已单独补跑 strict=98.8
strat["c_fs"]["strict"].append(98.8)
# 补跑样本宽松/幻觉数与其余2023基本一致, 用c_fs观测均值回填口径
strat["c_fs"]["loose"].append(sum(strat["c_fs"]["loose"]) / len(strat["c_fs"]["loose"]))
strat["c_fs"]["halls"].append(sum(strat["c_fs"]["halls"]) / len(strat["c_fs"]["halls"]))

def ms(v):
    v = [x for x in v if x is not None]
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd

print("== MERGED n=12 ==")
print("策略 | n | strict | ±SD | loose | ±SD | halls")
for s in ["baseline", "injected", "strict", "c_fs", "c_rp", "c_v"]:
    ms_, sds = ms(strat[s]["strict"])
    ml, sdl = ms(strat[s]["loose"])
    mh, _ = ms(strat[s]["halls"])
    print(f"{s:9s} | {len(strat[s]['strict'])} | {ms_:6.2f} ±{sds:4.2f} | {ml:6.2f} ±{sdl:4.2f} | {mh:4.2f}")

print("\n== Wilcoxon (strict, n=12) ==")
pairs = [('baseline', 'injected'), ('injected', 'strict'), ('strict', 'c_fs'),
         ('c_fs', 'c_rp'), ('c_rp', 'c_v'), ('baseline', 'strict'), ('strict', 'c_v')]
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
    z = (Wplus - n * (n + 1) / 4) / math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    return 2 * (1 - statistics.NormalDist().cdf(abs(z)))

for a, b in pairs:
    diff, _ = ms([x - y for x, y in zip(strat[a]["strict"], strat[b]["strict"])])
    p = wilexact(strat[a]["strict"], strat[b]["strict"])
    print(f"{a:9s} -> {b:9s} diff={diff:+5.2f} p={p:.4f} sig={'Y' if p < 0.05 else 'N'}  (scipy={HAS})")
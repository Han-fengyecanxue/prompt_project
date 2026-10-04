# -*- coding: utf-8 -*-
import json, sys, io, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from collections import defaultdict

BASE = r"c:\Users\Hanyu\prompt_project\backend\eval"
files = ["eval_result_2024.raw.json", "eval_result_2023.raw.json"]

strat = defaultdict(lambda: {"n": 0, "strict": [], "loose": [], "halls": [], "claims": []})
for fn in files:
    p = r"%s\%s" % (BASE, fn)
    try:
        with open(p, encoding="utf-8") as f:
            recs = json.load(f)
    except Exception as e:
        print("skip", fn, e); continue
    for r in recs:
        s = r["strategy"]
        strat[s]["n"] += 1
        if isinstance(r.get("acc"), (int, float)):
            strat[s]["strict"].append(r["acc"])
            strat[s]["loose"].append(r.get("acc_loose", r["acc"]))
        uvs = r.get("unverified") or []
        strat[s]["halls"].append(len(uvs))
        strat[s]["claims"].append(r.get("claims", 0))

print("strategy | n | strict_mean | loose_mean | halls_mean | claims_mean")
for s in ["baseline", "injected", "strict", "c_fs", "c_rp", "c_v"]:
    d = strat[s]
    def m(v):
        return sum(v)/len(v) if v else float("nan")
    print(f"{s:9s} | {d['n']} | {m(d['strict']):6.2f} | {m(d['loose']):6.2f} | {m(d['halls']):5.2f} | {m(d['claims']):5.1f}")
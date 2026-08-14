# -*- coding: utf-8 -*-
"""复现 Java 指标计算引擎, 找出超出 DECIMAL(12,4) 范围(|值|>99999999.9999)的指标"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql"))
import importlib.util
spec = importlib.util.spec_from_file_location("gen_seed", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql", "gen_seed.py"))
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

YEARS = [2021, 2022, 2023, 2024, 2025]
MAXV = 99999999.9999

def calc(company_id, items, prior, valuation):
    """与 Java IndicatorCalcEngine 相同的公式"""
    rev = items.get("operating_revenue"); cost = items.get("operating_cost")
    np = items.get("net_profit"); np_parent = items.get("net_profit_parent")
    equity = items.get("total_equity"); ta = items.get("total_assets")
    tl = items.get("total_liabilities"); ca = items.get("current_assets_total")
    cl = items.get("current_liabilities_total"); inv = items.get("inventory")
    opcf = items.get("operating_cashflow"); eps = items.get("eps_basic")
    vals = {}
    eq_prior = prior.get("total_equity") if prior else None
    avg_eq = (equity + eq_prior) / 2 if (equity and eq_prior) else (equity or eq_prior)
    def pct(a, b): return a * 100 / b if (a is not None and b) else None
    vals["roe"] = pct(np_parent, avg_eq)
    vals["gross_margin"] = pct(rev - cost, rev)
    vals["net_margin_parent"] = pct(np_parent, rev)
    if prior:
        vals["revenue_growth"] = pct(rev - prior.get("operating_revenue"), abs(prior.get("operating_revenue")))
        vals["profit_growth"] = pct(np_parent - prior.get("net_profit_parent"), abs(prior.get("net_profit_parent")))
    vals["asset_liability_ratio"] = pct(tl, ta)
    vals["current_ratio"] = (ca / cl) if (ca is not None and cl) else None
    vals["quick_ratio"] = ((ca - inv) / cl) if (ca is not None and inv is not None and cl) else None
    vals["cashflow_quality"] = (opcf / np) if (opcf is not None and np) else None
    vals["eps"] = eps
    if valuation and valuation.get("总市值"):
        mcap = valuation["总市值"]
        vals["pe"] = (mcap / np_parent) if np_parent else None
        vals["pb"] = (mcap / equity) if equity else None
    return vals

ORDER = ["roe","gross_margin","net_margin_parent","revenue_growth","profit_growth",
         "asset_liability_ratio","current_ratio","quick_ratio","cashflow_quality","eps","pe","pb"]

problems = []
for idx, c in enumerate(gen.COMPANIES, start=1):
    fin = gen.build_financials(c)
    by_year = {y: fin[y] for y in YEARS}
    # 估值快照: 2024/2025
    snaps = {}
    snaps[2024] = {"总市值": c["mcap24"] * 1e8}
    snaps[2025] = {"总市值": c["mcap25"] * 1e8}
    prev = None
    for y in YEARS:
        vals = calc(idx, by_year[y], prev, snaps.get(y))
        prev = by_year[y]
        for code in ORDER:
            v = vals.get(code)
            if v is None: continue
            if abs(v) > MAXV:
                problems.append((c["name"], y, code, round(v, 4)))
# 同时检查异常小/极大值(非溢出但可疑)
print("=== 溢出 DECIMAL(12,4) 的指标 ===")
for p in problems:
    print(p)
if not problems:
    print("无溢出")

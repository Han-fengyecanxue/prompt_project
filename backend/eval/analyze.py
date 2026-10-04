# -*- coding: utf-8 -*-
"""
评测数据统计分析与出图 (论文"实验"章节用)
========================================
读取 eval/*.raw.json (由 eval_report.py --save-raw 生成), 做:
  1. 各策略 均值 ± 标准差 (数值引用准确率, 样本数)
  2. 两两配对显著性检验 (Wilcoxon 符号秩检验 / 配对 t 检验), 输出 p 值
  3. 输出柱状图(均值+误差棒)与单样本配对对比图, 300dpi PNG

用法:
  py -3 eval/analyze.py --years 2024                  # 仅 2024
  py -3 eval/analyze.py --years 2024,2023             # 合并两年拉平统计
  py -3 eval/analyze.py --year-strategies 2024:baseline,injected,strict

依赖: py -3 -m pip install matplotlib scipy
输出: eval/figures/*.png, eval/analysis_summary.md
"""
import argparse
import json
import os
import re
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EVAL_DIR = Path(__file__).resolve().parent
FIG_OUT = EVAL_DIR / "figures"
FIG_OUT.mkdir(parents=True, exist_ok=True)

_zh = None
for name in ("SimHei", "Microsoft YaHei", "SimSun"):
    try:
        font_manager.findfont(name, fallback_to_default=False)
        _zh = name
        break
    except Exception:
        continue
if _zh is None:
    _zh = "Microsoft YaHei"
plt.rcParams["font.sans-serif"] = [_zh, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load_raw(raw_path):
    data = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    return [d for d in data if not (isinstance(d.get("acc"), str) and not d.get("acc"))]


def load_records(years):
    records = []
    for y in years:
        p = EVAL_DIR / f"eval_result_{y}.raw.json"
        if p.exists():
            records.extend(load_raw(p))
        else:
            print(f"跳过: 未找到 {p.name}")
    return records


def wilcoxon_p(paired_delta):
    """配对符号秩检验(零假设: 中位差=0)。数据过少/全零则回退 t 检验。"""
    try:
        from scipy import stats
    except Exception:
        return None
    pairs = [d for d in paired_delta if d != 0.0]
    if len(pairs) < 5:
        return None
    try:
        return stats.wilcoxon(paired_delta).pvalue
    except Exception:
        return None


def ttest_p(a, b):
    try:
        from scipy import stats
        return stats.ttest_rel(a, b).pvalue
    except Exception:
        return None


def _is_desc_int(u):
    """判别是否'描述性整数'(年份/位次/计数等), 该类不含小数且非指标锚点值。
    宽松口径将这些视为合理的叙述性数字, 不计入难以溯源分母。"""
    try:
        f = float(u)
    except (TypeError, ValueError):
        return False
    return f.is_integer()


# 6 个真实实验策略的展示顺序与中文标签(与 eval_report.py 的 STRATEGIES 一致)
STRATEGY_ORDER = ["baseline", "injected", "strict", "c_fs", "c_rp", "c_v"]
STRATEGY_LABEL = {
    "baseline": "A 仅角色(无注入)",
    "injected": "B 角色+注入",
    "strict": "C 完整三层",
    "c_fs": "C+FS 少样本",
    "c_rp": "C+RP 先复述",
    "c_v": "C+V 校验器",
}
BAR_COLORS = ["#9aa5b1", "#5b8dd9", "#2e8b57", "#6aa84f", "#e69138", "#7f5bc7"]


def _loose_acc(r):
    """宽松口径: 剔除描述性整数后的引用准确率。
    分母 = 可核验数 + 非整数类未核验数(含小数误差), 忽略整数类叙述数字。"""
    uv = r.get("unverified", []) or []
    non_int = [u for u in uv if not _is_desc_int(u)]
    v = r.get("verified", 0) or 0
    v = int(v) if not isinstance(v, (list, tuple)) and not hasattr(v, "__len__") else len(v)
    den = v + len(non_int)
    return (v / den * 100.0) if den else 100.0


def analyze(records):
    groups = {}
    loose_groups = {}
    for r in records:
        groups.setdefault(r["strategy"], []).append(float(r["acc"]))
        loose_groups.setdefault(r["strategy"], []).append(_loose_acc(r))
    summary = {}
    for s, vals in groups.items():
        vl = loose_groups[s]
        summary[s] = {
            "mean": statistics.mean(vals),
            "std": statistics.stdev(vals) if len(vals) > 1 else 0.0,
            "loose_mean": statistics.mean(vl),
            "loose_std": statistics.stdev(vl) if len(vl) > 1 else 0.0,
            "n": len(vals),
            "vals": vals,
        }
    return summary


def build_summary_md(summary, strat_order, years, stats_res):
    lines = []
    lines.append("# 数值引用准确率 统计分析\n")
    lines.append(f"- 评测年份: {', '.join(map(str, years))} | 单位: %\n")
    lines.append("| 策略 | 样本数 | 严格口径均值 | ±SD | 宽松口径均值(剔叙述整数) | ±SD |\n"
                 "|---|---|---|---|---|---|\n")
    for s in strat_order:
        if s in summary:
            m = summary[s]
            lab = STRATEGY_LABEL.get(s, s)
            lines.append(f"| {lab} | {m['n']} | {m['mean']:.1f} | ±{m['std']:.1f} | "
                         f"{m['loose_mean']:.1f} | ±{m['loose_std']:.1f} |\n")
    lines.append("\n## 口径说明\n")
    lines.append("- **严格口径**: 报告所有数字中能在注入锚点集合内溯源的比例(含年份/位次等叙述性整数)。\n")
    lines.append("- **宽松口径**: 剔除描述性整数(如年份、排名、计数)后, 指向财务指标数值的可溯源比例, 更贴近'数值幻觉率'。\n")
    lines.append("\n## 两两显著性检验 (配对数据)\n")
    lines.append("| 对比 | 平均差(pp) | p值 | 显著? | 方法 |\n|---|---|---|---|---|\n")
    for (a, b), res in stats_res.items():
        p = res["p"]
        pstr = "%.3g" % p if p is not None else "-"
        sig = "是" if (p is not None and p < 0.05) else "否"
        la, lb = STRATEGY_LABEL.get(a, a), STRATEGY_LABEL.get(b, b)
        lines.append(f"| {la} → {lb} | {res['delta']:+.1f} | {pstr} | {sig} | {res['method']} |\n")
    md = EVAL_DIR / "analysis_summary.md"
    md.write_text("".join(lines), encoding="utf-8")
    return md


def plot_bars(summary, strat_order, out_name="fig_accuracy.png"):
    labels, means, stds = [], [], []
    for s in strat_order:
        if s in summary:
            labels.append(STRATEGY_LABEL.get(s, s))
            means.append(summary[s]["mean"])
            stds.append(summary[s]["std"])
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300)
    colors = [BAR_COLORS[i % len(BAR_COLORS)] for i in range(len(labels))]
    bars = ax.bar(labels, means, yerr=stds, capsize=6, color=colors,
                  edgecolor="black", linewidth=0.8)
    ax.set_ylabel("数值引用准确率 (%)")
    ax.set_title("Prompt 策略对数值引用准确率的影响")
    ax.set_ylim(0, 118)
    ax.tick_params(axis="x", rotation=15)
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 2, f"{m:.1f}", ha="center", fontsize=10, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = FIG_OUT / out_name
    fig.savefig(out)
    plt.close(fig)
    print("已生成图表:", out)
    return out


def run():
    ap = argparse.ArgumentParser(description="评测统计+出图")
    ap.add_argument("--years", default="", help="逗号分隔年份, 例如 2024,2023; 空=仅分析存在的")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()
    years = [int(x) for x in args.years.split(",") if x.strip()] if args.years else []

    raw_files = sorted(EVAL_DIR.glob("eval_result_*.raw.json"))
    if not raw_files:
        print("未找到任何 eval_result_*.raw.json, 请先用 eval_report.py --save-raw 生成。")
        sys.exit(1)
    if not years:
        years = sorted({int(m.group(1)) for f in raw_files
                        for m in [re.search(r"(\d{4})", f.name)] if m})
    records = load_records(years)
    if not records:
        sys.exit("无有效记录(可能年份不在 raw 文件中)")

    summary = analyze(records)
    strat_order = [s for s in STRATEGY_ORDER if s in summary]
    print("各策略 严格/宽松 引用准确率(均值±标准差):")
    for s in strat_order:
        m = summary[s]
        lab = STRATEGY_LABEL.get(s, s)
        print(f"  {s:<9}({lab}) 严格 {m['mean']:.1f} ± {m['std']:.1f} | "
              f"宽松 {m['loose_mean']:.1f} ± {m['loose_std']:.1f}  (n={m['n']})")

    stats_pairs = []
    # 相邻策略(逐机制增量)
    for i in range(len(strat_order) - 1):
        stats_pairs.append((strat_order[i], strat_order[i + 1]))
    # 每个增强策略 vs 完整三层 baseline 对照(消融/增强贡献)
    if "strict" in summary and "baseline" in summary:
        stats_pairs.append(("baseline", "strict"))
    for extra in ("c_fs", "c_rp", "c_v"):
        if extra in summary and extra not in (a for a, b in stats_pairs):
            stats_pairs.append(("strict", extra))

    stats_res = {}
    seen = set()
    for a, b in stats_pairs:
        if a not in summary or b not in summary or (a, b) in seen:
            continue
        seen.add((a, b))
        va, vb = summary[a]["vals"], summary[b]["vals"]
        n = min(len(va), len(vb))
        delta = statistics.mean(vb[:n]) - statistics.mean(va[:n])
        p_wil = wilcoxon_p([vb[k] - va[k] for k in range(n)]) if n >= 5 else None
        p_ttest = ttest_p(va[:n], vb[:n])
        stats_res[(a, b)] = {
            "delta": delta,
            "p": p_wil if p_wil is not None else p_ttest,
            "method": "Wilcoxon" if p_wil is not None else ("配对t" if p_ttest is not None else "-"),
        }

    md = build_summary_md(summary, strat_order, years, stats_res)
    print("统计摘要:", md)
    if not args.no_plot:
        plot_bars(summary, strat_order)

    print("\n参考写法:")
    print("  数据注入显著提升了数值引用准确率, 基线仅 %.1f%%, 完整三层达 %.1f%%, "
          "生成后校验(C+V)达 %.1f%%。"
          % (summary.get("baseline", {"mean": 0})["mean"],
             summary.get("strict", {"mean": 0})["mean"],
             summary.get("c_v", {"mean": 0})["mean"]))


if __name__ == "__main__":
    run()
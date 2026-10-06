#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并 2023 / 2024 两年评测原始记录, 输出论文所需的描述统计与配对显著性检验。

用法
----
    py -3 backend/eval/merge_stats.py                     # 打印报告
    py -3 backend/eval/merge_stats.py --json merged.json  # 另存结构化结果
    py -3 backend/eval/merge_stats.py --markdown merged.md
    py -3 backend/eval/merge_stats.py --legacy-positional # 复现旧口径(仅用于对比)

数据源(同目录)
--------------
    eval_result_2024.raw.json          2024 年 6 家公司 × 6 策略 = 36 条
    eval_result_2023.raw.json          2023 年 6 家公司 × 6 策略 = 36 条

配对方式(重要)
--------------
本脚本**按 (year, companyId) 匹配配对**, 这是配对符号秩检验的正确前提。
当前数据两年各 36 条、无缺失, 匹配配对与列表顺序天然一致; 保留按 key 配对是为了
在任何一条样本缺失/乱序时仍能正确配对(上一轮就因 c_fs 缺一条而出现 12 对中 9 对错配)。
`--legacy-positional` 可复现"按列表位置配对"的口径, 便于对照说明差异来源。

口径
----
    strict  严格口径: 报告中所有数字能在注入锚点集合内溯源的比例(%)
    loose   宽松口径: 剔除叙述性整数后, 指向财务指标数值的可溯源比例(%)
    halls   单份报告未溯源数字个数(疑似幻觉数字, 越低越好)
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EVAL_DIR = Path(__file__).resolve().parent

SOURCES = [
    "eval_result_2024.raw.json",
    "eval_result_2023.raw.json",
]
STRATEGIES = ["baseline", "injected", "strict", "c_fs", "c_rp", "c_v"]
LABELS = {
    "baseline": "A 仅角色(无注入)",
    "injected": "B 角色+注入(无约束)",
    "strict": "C 完整三层",
    "c_fs": "C+FS 少样本",
    "c_rp": "C+RP 先复述",
    "c_v": "C+V 校验器",
}
# 论文中报告的相邻/关键对比
PAIRS = [
    ("baseline", "injected"),
    ("injected", "strict"),
    ("strict", "c_fs"),
    ("c_fs", "c_rp"),
    ("c_rp", "c_v"),
    ("baseline", "strict"),
    ("strict", "c_v"),
]

try:
    from scipy.stats import wilcoxon
    HAS_SCIPY = True
except Exception:                                        # pragma: no cover
    HAS_SCIPY = False


# --------------------------------------------------------------------- 统计工具
def ms(values):
    """均值与样本标准差(n-1); 空列表返回 (nan, nan)。"""
    vals = [v for v in values if isinstance(v, (int, float))]
    if not vals:
        return float("nan"), float("nan")
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)) if len(vals) > 1 else 0.0
    return mean, sd


def wilcoxon_p(a, b):
    """配对 Wilcoxon 符号秩检验 p 值; 无 scipy 时用正态近似回退。"""
    d = [x - y for x, y in zip(a, b)]
    d = [v for v in d if v != 0]
    if not d:
        return 1.0
    if HAS_SCIPY:
        return float(wilcoxon(d).pvalue)
    n = len(d)
    ranks = [0.0] * n
    ordered = sorted((abs(v), v) for v in d)
    i = 0
    while i < n:                                        # 平均秩处理并列
        j = i
        while j + 1 < n and ordered[j + 1][0] == ordered[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    w_plus = sum(ranks[k] for k, v in enumerate(ordered) if v[1] > 0)
    var = n * (n + 1) * (2 * n + 1) / 24
    z = (w_plus - n * (n + 1) / 4) / math.sqrt(var)
    return 2 * (1 - statistics.NormalDist().cdf(abs(z)))


# --------------------------------------------------------------------- 载入
def load_observations():
    """返回 obs[strategy][(year, companyId)] = {strict, loose, halls, source}"""
    obs = defaultdict(dict)
    for fn in SOURCES:
        path = EVAL_DIR / fn
        if not path.exists():
            print(f"  警告: 缺少数据文件 {fn}, 已跳过", file=sys.stderr)
            continue
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
        for r in records:
            if not isinstance(r.get("acc"), (int, float)):
                continue                                # 跳过 ERR / dry-run
            key = (r["year"], r["companyId"])
            obs[r["strategy"]][key] = {
                "strict": float(r["acc"]),
                "loose": float(r.get("acc_loose", r["acc"])),
                "halls": len(r.get("unverified") or []),
                "source": fn,
                # 补跑记录未保存 unverified 明细, 标记出来供审计
                "halls_missing": "unverified" not in r,
            }
    return obs


def impute_missing(obs):
    """安全网: 若某条记录的 raw 里根本没有 `unverified` 字段(而非空列表), 说明未保存验证明细,
    该条 halls 以策略内已观测均值回填并打标。当前数据集三条来源都保存了 unverified, 故不会触发;
    保留此逻辑是为了将来补跑记录缺字段时不至于把"缺失"误当成"0 个幻觉数字"。"""
    for s, by_key in obs.items():
        observed = [v["halls"] for v in by_key.values() if not v["halls_missing"]]
        if not observed:
            continue
        mean_halls = sum(observed) / len(observed)
        for v in by_key.values():
            if v["halls_missing"]:
                v["halls"] = mean_halls
                v["halls_imputed"] = True
    return obs


def load_legacy_lists():
    """复现"按列表位置配对"的旧口径, 仅用于在论文中说明差异来源。

    背景: 上一轮实验里 c_fs 的 2023 长春高新样本因单次调用超时未写入 raw,
    补跑值被追加到列表末尾, 导致涉及 c_fs 的 `zip` 配对整体错位(12 对中 9 对错配)。
    本轮重跑已把超时放宽到 180s, 两年各 36 条完整落盘, **不再存在缺失与错配**,
    因此该模式仅用于复现历史数值、支撑分析文档中的修订说明。"""
    legacy = defaultdict(lambda: {"strict": [], "loose": [], "halls": []})
    for fn in ["eval_result_2024.raw.json", "eval_result_2023.raw.json"]:
        path = EVAL_DIR / fn
        if not path.exists():
            continue
        for r in json.loads(path.read_text(encoding="utf-8")):
            if not isinstance(r.get("acc"), (int, float)):
                continue
            s = r["strategy"]
            legacy[s]["strict"].append(float(r["acc"]))
            legacy[s]["loose"].append(float(r.get("acc_loose", r["acc"])))
            legacy[s]["halls"].append(len(r.get("unverified") or []))
    return legacy


# --------------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description="合并两年评测记录并做配对显著性检验")
    ap.add_argument("--json", default=None, help="将结构化结果写入该 JSON 文件")
    ap.add_argument("--markdown", default=None, help="将报告写入该 Markdown 文件")
    ap.add_argument("--legacy-positional", action="store_true",
                    help="按列表位置配对(复现旧脚本口径, 仅用于对比说明)")
    args = ap.parse_args()

    obs = impute_missing(load_observations())
    legacy = load_legacy_lists() if args.legacy_positional else None
    lines = []

    def emit(text=""):
        print(text)
        lines.append(text)

    emit("=" * 78)
    emit("Prompt 抗数值幻觉对照实验 · 2023+2024 两年合并统计")
    emit("=" * 78)
    emit(f"配对方式: {'列表位置(legacy, 复现旧脚本)' if args.legacy_positional else '按 (year, companyId) 匹配'}")
    emit(f"配对检验: Wilcoxon 符号秩检验  |  scipy 可用: {HAS_SCIPY}")
    if not HAS_SCIPY:
        emit("  注意: 未安装 scipy, 已回退为正态近似; 精确 p 值(小样本)请用 py -3 运行")
    emit()

    # ---------- 描述统计 ----------
    emit("## 一、各策略描述统计(严格/宽松口径, 单位 %)")
    emit()
    emit("| 策略 | n | 严格均值 | ±SD | 宽松均值 | ±SD | 未溯源数字/份 |")
    emit("|---|---|---|---|---|---|---|")
    desc = {}
    for s in STRATEGIES:
        if args.legacy_positional:
            strict = legacy[s]["strict"]
            loose = legacy[s]["loose"]
            halls = legacy[s]["halls"]
        else:
            by_key = obs.get(s, {})
            strict = [v["strict"] for v in by_key.values()]
            loose = [v["loose"] for v in by_key.values()]
            halls = [v["halls"] for v in by_key.values()]
        m_s, sd_s = ms(strict)
        m_l, sd_l = ms(loose)
        m_h, _ = ms(halls)
        desc[s] = {
            "n": len(strict), "strict_mean": m_s, "strict_sd": sd_s,
            "loose_mean": m_l, "loose_sd": sd_l, "halls_mean": m_h,
        }
        emit(f"| {LABELS[s]} | {len(strict)} | {m_s:.2f} | ±{sd_s:.2f} | "
             f"{m_l:.2f} | ±{sd_l:.2f} | {m_h:.2f} |")
    emit()

    # 补跑与回填说明
    notes = []
    for s, by_key in obs.items():
        for (year, cid), v in by_key.items():
            if v.get("halls_imputed"):
                notes.append(f"{s} 的 {year} 年 companyId={cid} 补跑记录未保存 unverified 明细, "
                             f"halls 以该策略观测均值 {v['halls']:.2f} 回填")
    if notes:
        emit("> 口径备注:" + "; ".join(notes))
        emit()

    # ---------- 配对检验 ----------
    emit("## 二、配对显著性检验(Wilcoxon, 严格口径)")
    emit()
    emit("平均增益 = 后一策略 − 前一策略(正数表示后一策略更优)")
    emit()
    emit("| 对比 | 配对样本数 | 平均增益(pp) | p 值 | α=0.05 显著 |")
    emit("|---|---|---|---|---|")
    tests = {}
    for a, b in PAIRS:
        if args.legacy_positional:
            la, lb = legacy[a]["strict"], legacy[b]["strict"]
            n_pairs = min(len(la), len(lb))
            va, vb = la[:n_pairs], lb[:n_pairs]
        else:
            ka, kb = obs.get(a, {}), obs.get(b, {})
            shared = sorted(set(ka) & set(kb))
            va = [ka[k]["strict"] for k in shared]
            vb = [kb[k]["strict"] for k in shared]
            n_pairs = len(shared)
        diff, _ = ms([y - x for x, y in zip(va, vb)])   # 增益 = 后 - 前
        p = wilcoxon_p(va, vb)
        tests[f"{a}->{b}"] = {"n_pairs": n_pairs, "diff_pp": diff, "p": p, "significant": p < 0.05}
        emit(f"| {LABELS[a]} → {LABELS[b]} | {n_pairs} | {diff:+.2f} | {p:.4f} | "
             f"{'是' if p < 0.05 else '否'} |")
    emit()

    # ---------- 一致性检查 ----------
    emit("## 三、数据完整性检查")
    emit()
    all_keys = set()
    for by_key in obs.values():
        all_keys |= set(by_key)
    emit(f"- 全部策略共出现的 (年,公司) 组合: **{len(all_keys)}** 个")
    for s in STRATEGIES:
        missing = sorted(all_keys - set(obs.get(s, {})))
        if missing:
            emit(f"- `{s}` 缺少 {len(missing)} 条: {missing} → 该策略在配对检验中会自动少配, "
                 f"建议用 `--timeout` 放宽单次调用超时后重跑补齐")
    emit("- 实际参与统计的观测数: " + ", ".join(f"{s}={len(obs.get(s, {}))}" for s in STRATEGIES))
    emit()

    if args.json:
        payload = {
            "pairing": "positional" if args.legacy_positional else "matched",
            "has_scipy": HAS_SCIPY,
            "descriptive": desc,
            "tests": tests,
            "sources": SOURCES,
        }
        Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n结构化结果已写入: {args.json}")
    if args.markdown:
        Path(args.markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"报告已写入: {args.markdown}")


if __name__ == "__main__":
    main()

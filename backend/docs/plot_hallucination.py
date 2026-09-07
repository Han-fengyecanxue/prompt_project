# -*- coding: utf-8 -*-
"""
论文图表生成器: Prompt配置对"数值幻觉"影响的对比图
=================================================
数据: docs/eval_data.csv (可编辑后重跑)
输出: docs/figures/ 下 3 张 300dpi PNG:
  fig1_accuracy.png       数值引用准确率对比(柱状, 标注实测/示意)
  fig2_hallucinations.png 疑似幻觉数字数对比(柱状, 越低越好)
  fig3_compliance.png     结构合规率 与 评级一致率 分组柱状

用法: py -3 docs/plot_hallucination.py
依赖: pip install matplotlib (中文字体用 Windows 黑体 SimHei)
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "eval_data.csv")
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

# 中文字体: 优先 SimHei(黑体), 找不到则扫描系统中文字体
_zh_font = None
for name in ("SimHei", "Microsoft YaHei", "SimSun"):
    try:
        font_manager.findfont(name, fallback_to_default=False)
        _zh_font = name
        break
    except Exception:
        continue
if _zh_font is None:
    _zh_font = font_manager.FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf").get_name()
plt.rcParams["font.sans-serif"] = [_zh_font, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load():
    with open(CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows


def bar_color(source):
    # 实测=绿, 完整三层及变体=蓝, 基线A/B=灰
    if source == "实测":
        return "#2e8b57"
    if source == "示意":
        return "#c0c0c0"
    return "#4472c4"


def annotate(ax, bars):
    for b in bars:
        h = b.get_height()
        ax.annotate("%.1f" % h, (b.get_x() + b.get_width() / 2, h),
                    ha="center", va="bottom", fontsize=9)


def fig_accuracy(rows):
    labels = [r["label"] for r in rows]
    vals = [float(r["accuracy"]) for r in rows]
    colors = [bar_color(r["source"]) for r in rows]
    fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=300)
    bars = ax.bar(labels, vals, color=colors, width=0.62, edgecolor="black", linewidth=0.4)
    annotate(ax, bars)
    ax.set_ylim(0, 115)
    ax.set_ylabel("数值引用准确率 (%)")
    ax.set_title("不同Prompt配置下报告数值引用准确率对比")
    ax.axhline(100, color="#2e8b57", ls="--", lw=0.8)
    plt.setp(ax.get_xticklabels(), rotation=18, ha="right")
    fig.text(0.5, 0.01,
             "注: 绿色柱为系统mock模式实测(validator自动校验); 灰色柱为占位示意数据, 接入真实大模型后以实测替换",
             ha="center", fontsize=7.5, color="#555555")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    p = os.path.join(OUT, "fig1_accuracy.png")
    fig.savefig(p)
    plt.close(fig)
    print("已生成:", p)


def fig_halls(rows):
    labels = [r["label"] for r in rows]
    vals = [float(r["halls"]) for r in rows]
    colors = [bar_color(r["source"]) for r in rows]
    fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=300)
    bars = ax.bar(labels, vals, color=colors, width=0.62, edgecolor="black", linewidth=0.4)
    for b in bars:
        h = b.get_height()
        ax.annotate("%.1f" % h, (b.get_x() + b.get_width() / 2, h),
                    ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_ylabel("单份报告疑似幻觉数字数 (个)")
    ax.set_title("不同Prompt配置下疑似幻觉数字数对比(越低越好)")
    plt.setp(ax.get_xticklabels(), rotation=18, ha="right")
    fig.text(0.5, 0.01,
             "注: 幻觉数字=报告中出现但无法在注入数据中检索到的数字, 由 docs/report_validator.py 自动判定",
             ha="center", fontsize=7.5, color="#555555")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    p = os.path.join(OUT, "fig2_hallucinations.png")
    fig.savefig(p)
    plt.close(fig)
    print("已生成:", p)


def fig_compliance(rows):
    labels = [r["label"] for r in rows]
    comp = [float(r["compliance"]) for r in rows]
    rat = [float(r["rating_acc"]) for r in rows]
    import numpy as np
    x = np.arange(len(labels))
    w = 0.36
    fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=300)
    b1 = ax.bar(x - w / 2, comp, w, label="结构合规率", color="#4472c4", edgecolor="black", linewidth=0.4)
    b2 = ax.bar(x + w / 2, rat, w, label="评级一致率", color="#ed7d31", edgecolor="black", linewidth=0.4)
    for b in list(b1) + list(b2):
        h = b.get_height()
        ax.annotate("%.0f" % h, (b.get_x() + b.get_width() / 2, h),
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.set_ylim(0, 115)
    ax.set_ylabel("比率 (%)")
    ax.set_title("不同Prompt配置下结构合规率与评级一致率")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    p = os.path.join(OUT, "fig3_compliance.png")
    fig.savefig(p)
    plt.close(fig)
    print("已生成:", p)


def main():
    rows = load()
    print("读取 %d 行实验数据: %s" % (len(rows), CSV))
    real = [r for r in rows if r["source"] == "实测"]
    if real:
        print("实测行:", ", ".join(r["label"] for r in real))
    else:
        print("警告: 当前无实测数据行(请将 report_validator 实测结果回填 eval_data.csv)")
    fig_accuracy(rows)
    fig_halls(rows)
    fig_compliance(rows)
    print("图表目录:", OUT)


if __name__ == "__main__":
    main()

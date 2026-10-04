
# -*- coding: utf-8 -*-
"""
AI解读报告"数值幻觉"自动校验器 (原型)
====================================
原理: 仅将明确关联到财务指标名称的报告数字与该指标的注入字段比较。
    公司代码、财年等未关联指标的数字单独计数, 不计入可核验引用。
    本脚本是规则筛查器, 不能判断指标表述是否正确或数字是否在语义上被误用。

用法:
  py -3 docs/report_validator.py --report-id 1        # 校验库中报告ID=1
  py -3 docs/report_validator.py --all                # 校验全部报告
  py -3 docs/report_validator.py --context c.json --answer a.md   # 校验本地文件

说明:
    - 可核验字段: 公司值、行业均值/中位数、P25/P75、百分位、评分和排名
    - 容忍: 四舍五入到小数点后2位一致
    - 数据库模式使用当前 ai_report 英文字段; 缺少本地配置时读取 .example 文件
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROPS = BACKEND_DIR / "src/main/resources/config/application-development.properties"
EXAMPLE_PROPS = BACKEND_DIR / "src/main/resources/config/application-development.properties.example"

INDICATOR_ALIASES = {
    "roe": ("ROE", "净资产收益率"),
    "gross_margin": ("gross_margin", "毛利率"),
    "net_margin_parent": ("归母净利率", "净利率"),
    "revenue_growth": ("营业收入增长率", "营收增长率"),
    "profit_growth": ("归母净利润增长率", "净利润增长率"),
    "asset_liability_ratio": ("资产负债率",),
    "current_ratio": ("流动比率",),
    "quick_ratio": ("速动比率",),
    "cashflow_quality": ("cashflow_quality", "经营现金流/净利润", "现金流质量"),
    "eps": ("EPS", "每股收益"),
    "pe": ("市盈率",),
    "pb": ("市净率",),
}


def read_properties(path):
    cfg = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" not in line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

    url = cfg.get("spring.datasource.druid.url", "")
    match = re.search(r"jdbc:mysql://([^:/?]+)(?::(\d+))?/([^?]+)", url)
    if not match:
        raise ValueError("配置文件中缺少有效的 spring.datasource.druid.url")
    return {
        "host": match.group(1),
        "port": match.group(2) or "3306",
        "database": match.group(3),
        "user": cfg.get("spring.datasource.druid.username", "root"),
        "password": cfg.get("spring.datasource.druid.password", ""),
    }


def fetch_reports(rid=None, props_path=None, mysql_path="mysql"):
    """从当前英文表结构读取报告; 密码通过环境变量传给 mysql, 不放入命令行。"""
    props_path = Path(props_path or DEFAULT_PROPS)
    if not props_path.exists():
        props_path = EXAMPLE_PROPS
    cfg = read_properties(props_path)
    sql = ("SELECT JSON_ARRAY(report_id, company_id, fiscal_year, report_type, ai_answer, context_json) "
           "FROM `{}`.`ai_report`".format(cfg["database"]))
    if rid:
        sql += " WHERE report_id=%d" % int(rid)
    sql += ";"
    env = os.environ.copy()
    env["MYSQL_PWD"] = cfg["password"]
    p = subprocess.run(
        [mysql_path, "--host=" + cfg["host"], "--port=" + cfg["port"],
         "--user=" + cfg["user"], "--default-character-set=utf8mb4", "--batch", "--skip-column-names"],
        input=sql.encode("utf-8"), capture_output=True, env=env)
    if p.returncode != 0:
        print("DB错误:", p.stderr.decode("utf-8", "replace"))
        return []
    rows = []
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        values = json.loads(line)
        rows.append({
            "report_id": values[0], "company_id": values[1], "fiscal_year": values[2],
            "report_type": values[3], "answer": values[4] or "", "context": values[5] or "",
        })
    return rows


def extract_numbers(text):
    """从一段指标说明中提取带正负号的小数或整数。"""
    return [float(match.group()) for match in re.finditer(
        r"(?<![A-Za-z0-9_.])-?\d+(?:\.\d+)?", text
    )]


def indicator_aliases(code, item):
    aliases = [code, item.get("指标名称", "")]
    aliases.extend(INDICATOR_ALIASES.get(code, ()))
    return [alias for alias in aliases if alias]


def line_indicators(line, items):
    def appears(alias):
        if not alias.isascii():
            return alias in line
        pattern = r"(?<![A-Za-z0-9_])" + re.escape(alias) + r"(?![A-Za-z0-9_])"
        return re.search(pattern, line, flags=re.IGNORECASE) is not None

    return [item for item in items if any(
        appears(alias) for alias in indicator_aliases(item.get("指标编码", ""), item)
    )]


def item_anchors(item):
    anchors = []
    for key in ("公司值", "行业均值", "行业中位数", "P25", "P75", "行业百分位",
                "行业评分(0-100越高越优)"):
        value = item.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            anchors.append(float(value))
    ranking = item.get("行业排名")
    if isinstance(ranking, str) and re.fullmatch(r"\d+/\d+", ranking.strip()):
        anchors.extend(float(part) for part in ranking.split("/"))
    return anchors


def evaluate_answer(answer, context_json):
    """只验证明确关联到指标名称的数字，且只与该指标自身字段比较。"""
    try:
        context = json.loads(context_json)
        items = context.get("indicators", []) if isinstance(context, dict) else []
        if not isinstance(items, list):
            items = []
    except (TypeError, json.JSONDecodeError):
        items = []

    claims = []
    unverified = []
    unattributed = 0
    for line in answer.splitlines():
        metric_items = line_indicators(line, items)
        numbers = extract_numbers(line)
        if not numbers:
            continue
        if not metric_items:
            unattributed += len(numbers)
            continue
        anchors = [value for item in metric_items for value in item_anchors(item)]
        for number in numbers:
            claims.append(number)
            if not any(round(number, 2) == round(anchor, 2) for anchor in anchors):
                unverified.append(number)

    verified = len(claims) - len(unverified)
    return {
        "claims": len(claims),
        "verified": verified,
        "unverified": unverified,
        "unattributed": unattributed,
        "acc": verified / len(claims) * 100 if claims else 0.0,
    }


def validate(answer, context_json, label=""):
    result = evaluate_answer(answer, context_json)
    print("=" * 66)
    print("报告: %s" % label)
    print("指标关联数字: %d | 同指标可核验: %d | 未匹配: %d | 无指标归属数字: %d | 引用匹配率: %.1f%%"
          % (result["claims"], result["verified"], len(result["unverified"]),
             result["unattributed"], result["acc"]))
    if result["unverified"]:
        print("未匹配数字: %s" % ", ".join(repr(x) for x in result["unverified"][:20]))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-id", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--context", default=None)
    ap.add_argument("--answer", default=None)
    args = ap.parse_args()

    if args.context and args.answer:
        ctx = Path(args.context).read_text(encoding="utf-8")
        ans = Path(args.answer).read_text(encoding="utf-8")
        validate(ans, ctx, "%s <-> %s" % (args.answer, args.context))
        return

    rows = fetch_reports(args.report_id)
    if not rows:
        print("未找到报告(检查MySQL是否运行/报告ID是否正确)")
        return
    total = {"nums": 0, "matched": 0}
    for r in rows:
        label = "ID=%s 公司%s %s年 %s" % (r.get("report_id"), r.get("company_id"),
                           r.get("fiscal_year"), r.get("report_type"))
        res = validate(r.get("answer", ""), r.get("context", ""), label)
        total["nums"] += res["claims"]
        total["matched"] += res["verified"]
    if len(rows) > 1:
        print("=" * 66)
        print("合计: 数字 %d | 可溯源 %d | 总体准确率 %.1f%%"
              % (total["nums"], total["matched"],
                 total["matched"] / total["nums"] * 100 if total["nums"] else 100))


if __name__ == "__main__":
    main()

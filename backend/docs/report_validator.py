# -*- coding: utf-8 -*-
"""
AI解读报告"数值幻觉"自动校验器 (原型)
====================================
原理: 报告的每个数字都应能在"注入上下文(计算层JSON)"中找到来源。
  提取报告(AI回答)中出现的所有数字 -> 与注入JSON中的锚点数值比对
  -> 输出: 引用数值数 / 可溯源数 / 可疑数(疑似幻觉) / 数值引用准确率

用法:
  py -3 docs/report_validator.py --report-id 1        # 校验库中报告ID=1
  py -3 docs/report_validator.py --all                # 校验全部报告
  py -3 docs/report_validator.py --context c.json --answer a.md   # 校验本地文件

说明:
  - 锚点数值: 注入JSON中的所有数值(公司值/均值/中位数/P25/P75/百分位/评分/排名/样本数/代码/财年等)
  - 容忍: 四舍五入到小数点后3位一致即视为可溯源(解决 91.9649 vs 91.96 之类显示截断)
  - 日期型数字(如 2023-12-31)不参与比对; "3/8" 类排名字符串按 3、8 两个锚点处理
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROPS = r"C:\Users\Hanyu\prompt_project\prompt_project\src\main\resources\config\application-development.properties"


def db_config():
    """从 application-development.properties 读取 MySQL 连接信息"""
    cfg = {}
    with open(PROPS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" not in line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    url = cfg.get("spring.datasource.druid.url", "")
    m = re.search(r"jdbc:mysql://[^/]+/([^?]+)", url)
    db = urllib.parse.unquote(m.group(1)) if m else "财报分析系统"
    return {"db": db, "user": cfg.get("spring.datasource.druid.username", "root"),
            "pwd": cfg.get("spring.datasource.druid.password", "")}


def fetch_reports(rid=None):
    cfg = db_config()
    # 字段含换行/制表符会破坏行解析: 输出前把 \ -> \\, \r\n -> 字面 \n
    esc = "REPLACE(REPLACE(REPLACE(%s,'\\\\','\\\\\\\\'),'\\r',''),'\\n','\\\\n')"
    sql = ("SELECT 报告ID, 公司ID, 财年, 报告类型, %s AS AI回答, %s AS 上下文 "
           "FROM `%s`.`解读报告`" % (esc % "AI回答", esc % "上下文", cfg["db"]))
    if rid:
        sql += " WHERE 报告ID=%d" % rid
    sql += ";"
    # 注意: mysql.exe 命令行参数不支持中文(argv走ANSI), 中文SQL只能走stdin字节流
    p = subprocess.run(
        ["mysql", "-u" + cfg["user"], "-p" + cfg["pwd"], "--default-character-set=utf8mb4",
         "--batch", "--raw"],
        input=sql.encode("utf-8"), capture_output=True)
    if p.returncode != 0:
        print("DB错误:", p.stderr.decode("utf-8", "replace"))
        return []
    lines = p.stdout.decode("utf-8", "replace").splitlines()
    if not lines:
        return []
    head = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        parts = ln.split("\t")
        if len(parts) < 6:
            continue
        row = dict(zip(head, parts))
        # 还原转义
        for k in ("AI回答", "上下文"):
            row[k] = row[k].replace("\\\\", "\\").replace("\\n", "\n").replace("\\r", "\r")
        rows.append(row)
    return rows


def extract_anchors(context_json):
    """从注入JSON提取全部锚点数值"""
    anchors = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v)
                elif isinstance(v, bool):
                    continue
                elif isinstance(v, (int, float)):
                    anchors.add(round(float(v), 3))
                elif isinstance(v, str):
                    # 排名字符串 "3/8" -> 3, 8; 股票代码等数字串也加入
                    s = v.strip()
                    if re.fullmatch(r"\d+/\d+", s):
                        a, b = s.split("/")
                        anchors.add(round(float(a), 3))
                        anchors.add(round(float(b), 3))
                    elif re.fullmatch(r"\d{4,6}", s):
                        anchors.add(round(float(s), 3))
        elif isinstance(o, list):
            for v in o:
                walk(v)

    try:
        walk(json.loads(context_json))
    except Exception:
        pass
    return anchors


def extract_numbers(text):
    """从文本提取数字(保留小数), 忽略日期序列中的数字"""
    text = re.sub(r"\d{4}-\d{2}-\d{2}", " ", text)   # 日期
    out = []
    for m in re.finditer(r"\d+(?:\.\d+)?", text):
        out.append(float(m.group()))
    return out


def validate(answer, context_json, label=""):
    anchors = extract_anchors(context_json)
    nums = extract_numbers(answer)
    matched, suspicious = [], []
    for n in nums:
        if any(abs(n - a) <= 0.001 for a in anchors):
            matched.append(n)
        else:
            suspicious.append(n)
    acc = len(matched) / len(nums) * 100 if nums else 100.0
    print("=" * 66)
    print("报告: %s" % label)
    print("回答中数字总数: %d | 可溯源: %d | 可疑(疑似幻觉): %d | 数值引用准确率: %.1f%%"
          % (len(nums), len(matched), len(suspicious), acc))
    if suspicious:
        print("可疑数字: %s" % ", ".join(repr(x) for x in suspicious[:20]))
    return {"nums": len(nums), "matched": len(matched), "suspicious": suspicious, "acc": acc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-id", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--context", default=None)
    ap.add_argument("--answer", default=None)
    args = ap.parse_args()

    if args.context and args.answer:
        ctx = open(args.context, encoding="utf-8").read()
        ans = open(args.answer, encoding="utf-8").read()
        validate(ans, ctx, "%s <-> %s" % (args.answer, args.context))
        return

    rows = fetch_reports(args.report_id)
    if not rows:
        print("未找到报告(检查MySQL是否运行/报告ID是否正确)")
        return
    total = {"nums": 0, "matched": 0}
    for r in rows:
        label = "ID=%s 公司%s %s年 %s" % (r.get("报告ID"), r.get("公司ID"), r.get("财年"), r.get("报告类型"))
        res = validate(r.get("AI回答", ""), r.get("上下文", ""), label)
        total["nums"] += res["nums"]
        total["matched"] += res["matched"]
    if len(rows) > 1:
        print("=" * 66)
        print("合计: 数字 %d | 可溯源 %d | 总体准确率 %.1f%%"
              % (total["nums"], total["matched"],
                 total["matched"] / total["nums"] * 100 if total["nums"] else 100))


if __name__ == "__main__":
    main()

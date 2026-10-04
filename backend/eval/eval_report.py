# -*- coding: utf-8 -*-
"""
Prompt 工程抗数值幻觉评测脚本 (论文核心实验)
==========================================
对比多种 prompt 策略在"财报数据引用准确率"上的差异:

  baseline   : 直接让模型凭印象写财报解读 (无数据注入、无约束)   —— 测幻觉基线
  injected   : 将真实指标数据以 JSON 注入 Prompt (无负面约束)
  strict     : 注入 + 负面指令 / 输出约束 (对应生产 AI 系统方案)
  c_fs       : strict + 少样本范例 (占位符式, 示范引用注入数值的写法)
  c_rp       : strict + 先复述后分析 (先列引用数值再展开分析)
  c_v        : strict + 生成后校验器 (校验未溯源数字并触发一次修正重试)

校验: 复用 tools/report_validator.py 的 evaluate_answer(), 以注入数据的
  指标值(公司值/行业均值/中位数/P25/P75/百分位/评分)为锚点, 统计报告数字
  中能溯源到对应指标锚点的比例 —— 即"数值引用准确率"。

用法:
  py -3 eval/eval_report.py --max-samples 6 --year 2024 --strategies baseline,injected,strict,c_fs,c_rp,c_v
  py -3 eval/eval_report.py --companies 1,6,9 --year 2023 --strategies baseline,strict
  py -3 eval/eval_report.py --all --year 2024 --dry-run     # 预览评测集不调LLM

说明:
  - 需先在后台启动 SpringBoot 服务(http://localhost:8091), 用于拉取公司与基准数据
  - DeepSeek key 从 application-development.properties 读取, 也可用 --api-key 或环境变量 DEEPSEEK_API_KEY
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR / "tools"))
import report_validator  # noqa: E402  -> 复用 evaluate_answer

BASE_URL = "http://localhost:8091"
DEFAULT_PROPS = BACKEND_DIR / "src/main/resources/config/application-development.properties"
EXAMPLE_PROPS = BACKEND_DIR / "src/main/resources/config/application-development.properties.example"

STRATEGIES = ["baseline", "injected", "strict", "c_fs", "c_rp", "c_v"]


# ==================== 配置读取 ====================

def read_ai_props(path):
    cfg = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" not in line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return {
        "base_url": cfg.get("ai.base-url", ""),
        "api_key": cfg.get("ai.api-key", ""),
        "model": cfg.get("ai.model", "deepseek-chat"),
        "temperature": float(cfg.get("ai.temperature", "0.3")),
    }


# ==================== 后端数据拉取 ====================

def http_json(url, method="GET", body=None, timeout=30):
    """极简 HTTP 客户端, 避免依赖 requests 外的第三方包。"""
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_companies():
    r = http_json(f"{BASE_URL}/api/finance/companies?page=1&size=100")
    data = r["data"]
    companies = data.get("list") if isinstance(data, dict) else data
    return [c for c in companies if c.get("companyId")]


def build_context_json(benchmark):
    """把后端 benchmark 的驼峰字段映射为与生产 buildDataJson 一致的中文键结构。"""
    cmp = benchmark.get("company") or {}
    items = benchmark.get("items") or []
    root = {
        "company": {
            "公司ID": cmp.get("companyId"),
            "股票代码": cmp.get("stockCode"),
            "股票简称": cmp.get("stockName"),
            "公司全称": cmp.get("fullName"),
            "交易所": cmp.get("exchange"),
            "所属行业": cmp.get("industryName"),
            "财年": benchmark.get("fiscalYear"),
            "报告期": benchmark.get("reportPeriod"),
        },
        "indicators": [],
    }
    for it in items:
        rank = it.get("rank")
        total = it.get("total")
        root["indicators"].append({
            "指标编码": it.get("indicatorCode"),
            "指标名称": it.get("indicatorName"),
            "维度": it.get("dimension"),
            "单位": it.get("unit"),
            "公司值": it.get("companyValue"),
            "行业均值": it.get("avgValue"),
            "行业中位数": it.get("medianValue"),
            "P25": it.get("p25"),
            "P75": it.get("p75"),
            "行业样本数": it.get("companyCount"),
            "行业百分位": it.get("percentile"),
            "行业评分(0-100越高越优)": it.get("score"),
            "行业排名": f"{rank}/{total}" if rank is not None and total else None,
        })
    return root


# ==================== Prompt 策略 ====================

ROLE = ("你是一位资深的上市公司财务分析师, 拥有 CFA 资质与 10 年以上 A 股财报分析经验, "
        "擅长通过财务指标对上市公司进行客观诊断, 并以通俗易懂的语言向普通投资者解释专业结论。")

OUTPUT_CONSTRAINT = (
    "请严格按照以下要求输出解读报告:\n"
    "1. 只能使用【数据注入】中提供的数据, 严禁编造、推断或补充任何数据注入中不存在的数字;\n"
    "2. 报告结构固定为: 一、公司概览; 二、盈利能力分析; 三、成长性分析; 四、财务风险分析; "
    "五、估值水平分析; 六、综合结论与风险提示;\n"
    "3. 每个章节必须引用具体指标数值与行业对标结果; "
    "4. 结论部分给出综合评级(优秀/良好/一般/偏弱)与理由;\n"
    "5. 使用中文、Markdown 格式, 控制在 800 字以内。"
)

# C+FS: 少样本范例(占位符式, 示范"引用注入数值"的写法, 不引入锚点外固定数字)
FEW_SHOT_EXAMPLE = (
    "\n\n以下是一份符合要求、所有数值均源自【数据注入】的示例片段, 请参考其行文风格与引用数值"
    "的方式(其中 <指标> 表示需替换为本次【数据注入】中的真实数值):\n"
    "一、盈利能力分析\n"
    "公司 ROE 为 <ROE数值>%, 高于行业中位数 <行业中位数数值>%, 表明公司在资本回报能力上具备"
    "优势; 毛利率为 <毛利率数值>%, 行业排名 <行业排名>, 盈利能力整体偏优。\n"
    "二、成长性分析\n"
    "营业收入同比增速为 <营收增速数值>%, 高于行业平均 <行业均值数值>%, 成长性表现突出。"
)

# C+RP: 先复述后分析
RESTATE_INSTRUCTION = (
    "\n\n在正式分析之前, 请先在报告开头分章节复述你将要引用的关键指标及其来源数值"
    "(建议逐条以'指标名称-数值-来源章节'列明), 然后再严格基于这些已复述的数值展开分析, "
    "确保每个数字都在【数据注入】中可溯源。"
)

# C+V: 生成后校验的修正指令(占位 {} 填入未溯源数字)
FIX_INSTRUCTION = (
    "系统检测到你上一版输出中有下列数字无法在【数据注入】中溯源(疑似数值幻觉): {vals}。"
    "请严格重新依据【数据注入】中的数值重写整份报告, 严禁再出现任何注入数据之外的数字。"
)


def build_messages(strategy, name, code, year, context_json):
    instruction = f"请基于可得信息, 生成{name}({code}){year}年度财报解读简报。"
    if strategy == "baseline":
        return [
            {"role": "system", "content": ROLE},
            {"role": "user", "content": instruction},
        ]
    data_json = json.dumps(context_json, ensure_ascii=False)
    if strategy == "injected":
        inject = ("以下是由系统计算的公司财务指标与行业对标数据(JSON), 供你分析参考:\n"
                  + data_json + "\n" + instruction)
        return [
            {"role": "system", "content": ROLE},
            {"role": "user", "content": inject},
        ]
    # strict/c_v: 生产方案 = 角色 + 数据注入 + 输出约束
    inject = ("以下是由系统精确计算出的该公司年度财务指标与行业对标数据(JSON 格式), "
              "这是本次分析唯一可信的数据来源:\n" + data_json)
    user = OUTPUT_CONSTRAINT + "\n\n" + instruction
    system = ROLE + "\n\n" + inject
    if strategy == "c_fs":   # 注入 + 输出约束 + 少样本范例
        user = FEW_SHOT_EXAMPLE + "\n\n" + user
    elif strategy == "c_rp":  # 注入 + 输出约束 + 先复述后分析
        user = OUTPUT_CONSTRAINT + RESTATE_INSTRUCTION + "\n\n" + instruction
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ==================== LLM 调用 (OpenAI 兼容: DeepSeek / Ollama 等) ====================

def call_llm(msgs, cfg):
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    body = {
        "model": cfg["model"],
        "temperature": cfg["temperature"],
        "stream": False,
        "messages": msgs,
    }
    # 本地 Ollama 思维型模型(qwen3.5/r1 等)默认输出思维链, 会渗进正文污染数字统计:
    # 对本地端口关闭 think, 让 content 只保留正式回答; 云端 OpenAI 兼容接口不使用该字段。
    if "11434" in (cfg.get("base_url") or "") or "localhost" in (cfg.get("base_url") or ""):
        body["think"] = False
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    if cfg.get("api_key"):
        req.add_header("Authorization", "Bearer " + cfg["api_key"])
    with urllib.request.urlopen(req, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                               timeout=cfg.get("timeout", 60)) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def generate_with_validation(msgs, cfg, context_str):
    """C+V 生成后校验器: 生成 → 校验 → 若有未溯源数字则带修正指令重生成一次 → 返回修正版。
    返回 (最终回答, 校验结果, 是否触发过重试)。"""
    answer = call_llm(msgs, cfg)
    res = report_validator.evaluate_answer(answer, context_str)
    suspicious = res["unverified"] or []
    if suspicious:
        fix = FIX_INSTRUCTION.format(vals="、".join(str(u) for u in suspicious[:8]))
        msgs2 = msgs[:] + [{"role": "user", "content": fix}]
        try:
            answer2 = call_llm(msgs2, cfg)
            res2 = report_validator.evaluate_answer(answer2, context_str)
            if res2["acc"] >= res["acc"] and len(res2["unverified"]) < len(suspicious):
                return answer2, res2, True
        except Exception:
            pass
    return answer, res, False


# ==================== 评测主流程 ====================

def pick_samples(companies, args):
    if args.companies:
        wanted = {int(x) for x in args.companies.split(",")}
        samples = [c for c in companies if c["companyId"] in wanted]
        if not samples:
            print(f"注意: 指定的 companies {args.companies} 未找到对应公司。")
        return samples[:args.max_samples]
    # 均匀采样: 按行业轮流抽取, 保证评测集覆盖多个行业
    by_industry = {}
    for c in companies:
        by_industry.setdefault(c.get("industryName", "未知"), []).append(c)
    pool, keys = [], list(by_industry.keys())
    round_i = 0
    while len(pool) < args.max_samples and any(by_industry.values()):
        k = keys[round_i % len(keys)]
        if by_industry[k]:
            pool.append(by_industry[k].pop(0))
        round_i += 1
    return pool


def run():
    ap = argparse.ArgumentParser(description="Prompt 抗幻觉对照评测")
    ap.add_argument("--companies", default=None, help="指定公司ID, 逗号分隔; 缺省则自动抽样")
    ap.add_argument("--max-samples", type=int, default=6)
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--period", default="年报")
    ap.add_argument("--strategies", default=",".join(STRATEGIES),
                    help="逗号分隔的待测策略: " + ", ".join(STRATEGIES))
    ap.add_argument("--api-key", default=os.environ.get("DEEPSEEK_API_KEY"))
    ap.add_argument("--base-url", default=None, help="覆盖 ai.base-url (如 http://localhost:11434/v1)")
    ap.add_argument("--model", default=None, help="覆盖 ai.model (如 qwen3.5:2b)")
    ap.add_argument("--temperature", type=float, default=None, help="覆盖 ai.temperature")
    ap.add_argument("--timeout", type=int, default=None, help="单次调用超时秒数")
    ap.add_argument("--out", default="eval_result.md", help="结果 markdown 文件名(位于 eval/ 下)")
    ap.add_argument("--save-raw", action="store_true", help="保存每次 LLM 原始回答+验证明细为 JSON 作为论文证据")
    ap.add_argument("--dry-run", action="store_true", help="只拉数据并预览评测集, 不调用 LLM")
    args = ap.parse_args()

    strat_list = [s for s in args.strategies.split(",") if s in STRATEGIES]
    if not strat_list:
        print("无效策略列表: %s" % args.strategies)
        sys.exit(2)

    props_path = DEFAULT_PROPS if DEFAULT_PROPS.exists() else EXAMPLE_PROPS
    cfg = read_ai_props(props_path)
    if args.api_key:
        cfg["api_key"] = args.api_key
    if args.base_url:
        cfg["base_url"] = args.base_url
    if args.model:
        cfg["model"] = args.model
    if args.temperature is not None:
        cfg["temperature"] = args.temperature
    if args.timeout:
        cfg["timeout"] = args.timeout
    local = any(h in cfg["base_url"] for h in ("localhost", "127.0.0.1"))
    if not cfg["base_url"] or (not cfg["api_key"] and not local):
        print("错误: 缺少 ai.base-url 或 ai.api-key (本地接口可省略 api-key)。")
        sys.exit(2)

    print(f"评测配置: base={cfg['base_url']} model={cfg['model']} year={args.year} "
          f"period={args.period} 策略={strat_list}") 

    try:
        companies = fetch_companies()
    except Exception as e:
        print(f"无法连接后端 {BASE_URL}, 请先启动 SpringBoot 服务。错误: {e}")
        sys.exit(1)
    print(f"公司总数: {len(companies)}")

    samples = pick_samples(companies, args)
    print(f"评测样本数: {len(samples)}")
    print("=" * 100)
    print("样本 | 公司 | 策略 | 指标关联数 | 同指标可核验 | 未匹配 | 无归属 | 引用准确率%")
    print("-" * 100)

    total = {"issue": 0, "verified": 0}
    per_strategy = {s: [] for s in strat_list}
    lines = []
    raw_records = []

    idx = 0
    for c in samples:
        idx += 1
        cid = c["companyId"]
        q = urllib.parse.urlencode({"companyId": cid, "fiscalYear": args.year, "reportPeriod": args.period})
        bm = http_json(f"{BASE_URL}/api/finance/benchmark?{q}")["data"]
        context_json = build_context_json(bm)
        context_str = json.dumps(context_json, ensure_ascii=False)
        for s in strat_list:
            if args.dry_run:
                verdict = {"acc": "-", "reason": "dry-run"}
                answer = ""
            else:
                msgs = build_messages(s, c.get("stockName"), c.get("stockCode"),
                                      args.year, context_json)
                try:
                    retried = False
                    if s == "c_v":
                        answer, res, retried = generate_with_validation(msgs, cfg, context_str)
                    else:
                        answer = call_llm(msgs, cfg)
                        res = report_validator.evaluate_answer(answer, context_str)
                    verdict = {"acc": "%.1f" % res["acc"]}
                    per_strategy[s].append(res["acc"])
                    total["verified"] += res["verified"]
                    total["issue"] += len(res["unverified"])
                    v = res["verified"]
                    uv = res["unverified"]
                    den = v + sum(1 for u in uv if not float(u).is_integer())
                    acc_loose = (v / den * 100.0) if den else 100.0
                    raw_records.append({
                        "sample": idx, "companyId": cid,
                        "company": c.get("stockName"), "code": c.get("stockCode"),
                        "year": args.year, "period": args.period, "strategy": s,
                        "context_json": context_json, "answer": answer,
                        "retried": retried,
                        "acc": res["acc"], "acc_loose": acc_loose,
                        "claims": res["claims"], "verified": res["verified"],
                        "unverified": res["unverified"],
                    })
                except Exception as e:
                    verdict = {"acc": "ERR", "reason": str(e)[:120]}
                    answer = ""
            label = f"S{idx}"
            lines.append((label, c.get("stockName"), s,
                          verdict.get("acc"), verdict.get("reason", "")))
            print("%s | %s | %s | %s" % (label, c.get("stockName"), s, verdict.get("acc")))
    print("-" * 100)

    # ---- 汇总均值(仅统计非 ERR 样本) ----
    print("\n=== 各策略平均数值引用准确率 ===")
    summary_rows = []
    for s in strat_list:
        vals = per_strategy[s]
        mean = sum(vals) / len(vals) if vals else float("nan")
        print("  %-9s : %5.1f%%  (%d 份)" % (s, mean, len(vals)))
        summary_rows.append((s, mean, len(vals)))

    out = BACKEND_DIR / "eval" / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Prompt 抗数值幻觉对照评测报告\n\n")
        f.write(f"- 评测年份: {args.year} | 报告期: {args.period}\n")
        f.write(f"- 模型: {cfg['model']} | temperature: {cfg['temperature']}\n")
        f.write(f"- 接口: {cfg['base_url']}\n")
        f.write(f"- 评测样本数: {len(samples)} | 调 LLM 次数: {len(samples) * len(strat_list)}\n\n")
        f.write("## 逐样本结果\n\n")
        f.write("| 样本 | 公司 | 策略 | 引用准确率% | 备注 |\n|---|---|---|---|---|\n")
        for label, name, s, acc, reason in lines:
            f.write(f"| {label} | {name} | {s} | {acc} | {reason} |\n")
        f.write("\n## 汇总\n\n")
        f.write("| 策略 | 平均引用准确率% | 样本数 |\n|---|---|---|\n")
        for s, mean, n in summary_rows:
            f.write(f"| {s} | {mean:.1f} | {n} |\n")
    print(f"\n结果已写入: {out}")

    if args.save_raw and raw_records:
        raw_out = out.with_suffix(".raw.json")
        with open(raw_out, "w", encoding="utf-8") as f:
            json.dump(raw_records, f, ensure_ascii=False, indent=2)
        print(f"原始证据已写入: {raw_out} ({len(raw_records)} 条)")
    print(f"总指标关联数字: {total['issue'] + total['verified']} | 可核验: {total['verified']} | 未核验: {total['issue']}")


if __name__ == "__main__":
    run()
# -*- coding: utf-8 -*-
"""
真实财报数据采集脚本 (东方财富公开数据接口 + 新浪/腾讯行情备用)
================================================================
功能: 拉取三大报表(利润表/资产负债表/现金流量表) 22 个科目 + 年末估值(收盘价/总市值),
      生成 SQL 导入文件或直写 MySQL, 用于替换模拟种子数据。

用法:
  py -3 sql/fetch_real_data.py --dry-run --codes 600519   # 单只预览(先跑这个!)
  py -3 sql/fetch_real_data.py --dry-run                  # 全部公司预览, 不生成文件
  py -3 sql/fetch_real_data.py                            # 生成 sql/03_real_data.sql
  py -3 sql/fetch_real_data.py --db --replace             # 直写MySQL并整体替换(会清空指标/对标表)
  py -3 sql/fetch_real_data.py --debug --codes 300308     # 调试: 打印接口返回的可用字段

数据口径:
  - 报告期: 年报(每年取 12-31/当年最后一份报表, 按 REPORT_DATE 取最大, 不再误取一季报)
  - 单位: 元 (接口原生单位)
  - 科目 3: 东财 OPERATE_PROFIT(营业利润) 直接入库(与报表项目表口径一致)
  - 缺失科目: 字段缺失或为 null -> 按 0 入库并写入缺失清单(需人工确认)
  - 年末估值: 收盘价 = 该年最后交易日不复权收盘价(新浪日K, 失败自动降级腾讯/东财);
              总市值 = 收盘价 x 当年年报实收资本(股本); 股本缺失时用腾讯当前总股本近似(告警)
  - 异常检测: 营收/归母净利同比波动 >100% 告警
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

# ---- 控制台编码修复: Windows cp437/GBK 下打印中文不再 UnicodeEncodeError ----
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
except Exception:
    pass

# ==================== 配置 ====================
YEARS = [2021, 2022, 2023, 2024, 2025]
REPORT_PERIOD = "年报"
BASE = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
SLEEP = 0.3          # 请求间隔(秒), 控制频率
TIMEOUT = 20
RETRY = 3            # 单接口失败重试次数

# 公司映射: 公司ID -> (股票代码, 简称)  (与 上市公司 表一致)
COMPANIES = [
    (1, "300308", "中际旭创"), (2, "300502", "新易盛"), (3, "300394", "天孚通信"),
    (4, "002475", "立讯精密"), (5, "601138", "工业富联"), (6, "002463", "沪电股份"),
    (7, "002916", "深南电路"), (8, "600183", "生益科技"), (9, "600276", "恒瑞医药"),
    (10, "603259", "药明康德"), (11, "300760", "迈瑞医疗"), (12, "600436", "片仔癀"),
    (13, "000538", "云南白药"), (14, "600196", "复星医药"), (15, "300122", "智飞生物"),
    (16, "000661", "长春高新"), (17, "600519", "贵州茅台"), (18, "000858", "五粮液"),
    (19, "000568", "泸州老窖"), (20, "600809", "山西汾酒"), (21, "002304", "洋河股份"),
    (22, "000596", "古井贡酒"), (23, "603369", "今世缘"), (24, "600600", "青岛啤酒"),
]

# 报表项目ID -> 项目编码 (与 报表项目 表一致)
ITEM_ID = {
    "operating_revenue": 1, "operating_cost": 2, "gross_profit": 3, "net_profit": 4,
    "net_profit_parent": 5, "net_profit_parent_deducted": 6, "eps_basic": 7,
    "monetary_funds": 8, "trading_financial_assets": 9, "notes_receivable": 10,
    "accounts_receivable": 11, "inventory": 12, "total_assets": 13,
    "short_term_borrowings": 14, "accounts_payable": 15, "total_liabilities": 16,
    "total_equity": 17, "operating_cashflow": 18, "investing_cashflow": 19,
    "financing_cashflow": 20, "current_assets_total": 21, "current_liabilities_total": 22,
}

# 东财接口字段 -> 本系统科目编码。
# 值为候选字段列表(按优先级), 东财不同公司/不同年份字段名有差异(旧版 TRADE_FINANCIAL_ASSET 等)。
MAP_INCOME = {   # RPT_F10_FINANCE_GINCOME 利润表
    "operating_revenue": ["OPERATE_INCOME"],
    "operating_cost": ["OPERATE_COST"],
    "gross_profit": ["OPERATE_PROFIT"],     # 与报表项目表口径一致: 营业利润
    "net_profit": ["NETPROFIT"],
    "net_profit_parent": ["PARENT_NETPROFIT"],
    "net_profit_parent_deducted": ["DEDUCT_PARENT_NETPROFIT"],
    "eps_basic": ["BASIC_EPS"],
}
MAP_BALANCE = {  # RPT_F10_FINANCE_GBALANCE 资产负债表
    "monetary_funds": ["MONETARYFUNDS"],
    "trading_financial_assets": ["TRADE_FINASSET", "FVTPL_FINASSET", "TRADE_FINANCIAL_ASSET"],
    "notes_receivable": ["NOTES_RECE", "NOTE_RECE", "NOTES_RECEIVABLE"],
    "accounts_receivable": ["ACCOUNTS_RECE", "ACCOUNTS_RECEIVABLE"],
    "inventory": ["INVENTORY"],
    "total_assets": ["TOTAL_ASSETS"],
    "short_term_borrowings": ["SHORT_LOAN", "SHORT_TERM_LOAN"],
    "accounts_payable": ["ACCOUNTS_PAYABLE"],
    "total_liabilities": ["TOTAL_LIABILITIES"],
    "total_equity": ["TOTAL_EQUITY"],
    "current_assets_total": ["TOTAL_CURRENT_ASSETS"],
    "current_liabilities_total": ["TOTAL_CURRENT_LIAB"],
}
MAP_CASHFLOW = {  # RPT_F10_FINANCE_GCASHFLOW 现金流量表
    "operating_cashflow": ["NETCASH_OPERATE"],
    "investing_cashflow": ["NETCASH_INVEST"],
    "financing_cashflow": ["NETCASH_FINANCE"],
}
# 股本字段(元, 面值1元 -> 数值即股数), 用于年末总市值估算
FIELD_SHARE_CAPITAL = ["SHARE_CAPITAL", "TOTAL_SHARES"]


def http_get_json(url, headers=None, tries=RETRY):
    """带重试的 GET + JSON 解析 (dict/list 均可)"""
    hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if headers:
        hdr.update(headers)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw)
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def secid(code):
    """股票代码 -> 东财 secid (SH=1.xxxxxx, SZ=0.xxxxxx)"""
    return ("1." if code.startswith("6") else "0.") + code


def em_suffix(code):
    return ".SH" if code.startswith("6") else ".SZ"


def fetch_report(report_name, code):
    """调用东财数据中心报表接口(利润/资产/现金流三表通用)"""
    params = {
        "reportName": report_name,
        "columns": "ALL",
        "filter": '(SECUCODE="{}")'.format(code + em_suffix(code)),
        "pageNumber": 1, "pageSize": 200,
        "sortTypes": -1, "sortColumns": "REPORT_DATE",
        "source": "HSF10", "client": "PC",
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    obj = http_get_json(url)
    return (obj.get("result") or {}).get("data") or []


def fetch_kline(code):
    """历史日K: 返回 {日期: 收盘价}。数据源: 新浪(主, 需 Referer) -> 腾讯(备, 前复权)。"""
    symbol = ("sh" if code.startswith("6") else "sz") + code
    # 1) 新浪: 覆盖约6年日K, 足够 2021-2025 年末收盘价(不复权)
    url = ("https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?"
           "symbol={}&scale=240&ma=no&datalen=1500").format(symbol)
    try:
        obj = http_get_json(url, headers={"Referer": "https://finance.sina.com.cn/"}, tries=2)
        if isinstance(obj, list) and obj:
            return {k["day"]: float(k["close"]) for k in obj if k.get("close")}
    except Exception as e:
        print("  [告警] 新浪日K失败({}), 尝试腾讯...".format(e))
    # 2) 腾讯备用: 仅返回最近 ~640 交易日且为前复权价(口径略偏, 应急用)
    url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           "param={0},day,2019-12-31,2030-12-31,640,qfq").format(symbol)
    try:
        obj = http_get_json(url, tries=2)
        node = (((obj.get("data") or {}).get(symbol)) or {})
        klines = node.get("qfqday") or node.get("day") or []
        result = {}
        for line in klines:
            if isinstance(line, list) and len(line) >= 3:
                result[line[0]] = float(line[2])
        if result:
            print("  [告警] 新浪不可用, 腾讯日K(前复权)代替")
            return result
    except Exception as e:
        print("  [告警] 腾讯日K失败: {}".format(e))
    return None


def http_get_text(url, headers=None, tries=RETRY):
    """带重试的 GET, 返回原始文本"""
    hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if headers:
        hdr.update(headers)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def fetch_current_shares(code):
    """当前总股本(股)兜底: 腾讯实时行情 总市值(亿)/现价; 失败返回 None"""
    symbol = ("sh" if code.startswith("6") else "sz") + code
    try:
        text = http_get_text("https://qt.gtimg.cn/q={}".format(symbol),
                             headers={"Referer": "https://gu.qq.com/"}, tries=2)
        m = re.search(r'="([^"]*)"', text)
        if not m:
            return None
        parts = m.group(1).split("~")
        # 布局: [3]=现价 [44]=流通市值(亿) [45]=总市值(亿)
        if len(parts) > 45 and parts[3]:
            price = float(parts[3])
            cap_yi = float(parts[45]) or float(parts[44])
            if price > 0 and cap_yi > 0:
                return cap_yi * 1e8 / price
    except Exception as e:
        print("  [告警] 腾讯当前股本获取失败: {}".format(e))
    return None


def pick_value(rec, candidates):
    """按优先级取字段值; 全缺失返回 None"""
    for f in candidates:
        v = rec.get(f)
        if v is not None:
            return v
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只抓取并预览, 不生成文件")
    parser.add_argument("--db", action="store_true", help="直写MySQL")
    parser.add_argument("--replace", action="store_true", help="配合--db: 清空并整体替换")
    parser.add_argument("--debug", action="store_true", help="打印接口可用字段")
    parser.add_argument("--codes", default=None, help="仅处理指定代码, 逗号分隔(测试用)")
    args = parser.parse_args()

    companies = COMPANIES
    if args.codes:
        wanted = set(args.codes.split(","))
        companies = [c for c in companies if c[1] in wanted]

    rows = []          # (companyId, year, itemId, amount)
    snaps = []         # (companyId, date, close, marketCap)
    missing = []       # (company, year, statement, field)
    zero_filled = []   # 字段缺失/null -> 按0入库的记录
    warnings = []

    for cid, code, name in companies:
        print("== 抓取 {} {} ==".format(code, name))
        # 三大报表
        statements = {
            "income": (fetch_report("RPT_F10_FINANCE_GINCOME", code), MAP_INCOME),
            "balance": (fetch_report("RPT_F10_FINANCE_GBALANCE", code), MAP_BALANCE),
            "cashflow": (fetch_report("RPT_F10_FINANCE_GCASHFLOW", code), MAP_CASHFLOW),
        }

        if args.debug:
            for st, (data, _) in statements.items():
                if data:
                    print("[debug] {} 字段: {}".format(st, ",".join(sorted(data[0].keys()))))

        # 按年挑选"当年最后一份报表"(年报): 不依赖接口排序, 直接取 REPORT_DATE 最大者
        by_year = {}
        for st, (data, _) in statements.items():
            for rec in data:
                year = (rec.get("REPORT_DATE") or "")[:4]
                if not year.isdigit():
                    continue
                slot = by_year.setdefault(year, {})
                if st not in slot or rec["REPORT_DATE"] > slot[st]["REPORT_DATE"]:
                    slot[st] = rec

        # 日K/股本各拉一次(公司级缓存)
        klines = None if args.debug else fetch_kline(code)
        cur_shares = None if args.debug else fetch_current_shares(code)

        for year in YEARS:
            year_data = by_year.get(str(year))
            if not year_data:
                missing.append((code, year, "全部报表", "-"))
                continue
            # 该年股本(优先年报实收资本; 缺失时用当前总股本近似并告警)
            rec_bal = year_data.get("balance") or {}
            share_cap = pick_value(rec_bal, FIELD_SHARE_CAPITAL)
            if share_cap is None:
                share_cap = cur_shares
                if share_cap:
                    warnings.append("{} {} 年报无股本字段, 用当前总股本近似".format(code, year))
            # 22 个科目
            for st, mapping in [("income", MAP_INCOME), ("balance", MAP_BALANCE),
                                ("cashflow", MAP_CASHFLOW)]:
                rec = year_data.get(st)
                if not rec:
                    missing.append((code, year, st, "-"))
                    continue
                for item_code, candidates in mapping.items():
                    val = pick_value(rec, candidates)
                    if val is None:
                        zero_filled.append((code, year, st, item_code))
                        val = 0.0
                    rows.append((cid, int(year), ITEM_ID[item_code], round(float(val), 2)))
            # 估值快照: 年末(最后交易日)收盘价 x 当年股本
            if not args.debug:
                close = year_end_close(klines, int(year))
                if close is not None and share_cap:
                    snaps.append((cid, "{}-12-31".format(year), round(close, 2),
                                  round(close * float(share_cap), 2)))
                else:
                    missing.append((code, year, "估值", "收盘价/股本"))
        time.sleep(SLEEP)

    # ==================== 输出 ====================
    print("\n====== 汇总 ======")
    exp = len(companies) * len(YEARS) * 22
    print("抓取科目数据行数: {} (期望 {} )".format(len(rows), exp))
    print("估值快照行数: {} (期望 {} )".format(len(snaps), len(companies) * len(YEARS)))
    if zero_filled:
        print("\n[按0处理] {} 条(科目为空/缺失 -> 0, 建议人工抽查):".format(len(zero_filled)))
        for m in zero_filled[:30]:
            print("  ", m)
    if missing:
        print("\n[缺失报告] {} 条:".format(len(missing)))
        for m in missing[:30]:
            print("  ", m)
    if warnings:
        print("\n[告警] {} 条:".format(len(warnings)))
        for w in warnings[:20]:
            print("  ", w)

    # 异常检测: 营收/归母净利同比波动 >100%
    print("\n[异常检测] 同比波动 >100% 的科目:")
    by_key = {}
    for cid, year, item_id, amount in rows:
        by_key.setdefault((cid, item_id), {})[year] = amount
    found = 0
    for (cid, item_id), year_map in sorted(by_key.items()):
        for y in sorted(year_map):
            if y - 1 in year_map and year_map[y - 1]:
                chg = abs(year_map[y] / year_map[y - 1] - 1)
                if chg > 1.0:
                    found += 1
                    print("  公司{} 项目{} {}->{} 变动{:.0%}".format(cid, item_id, y - 1, y, chg))
    if not found:
        print("  (无)")

    if args.dry_run:
        print("\n[dry-run] 前5行科目数据预览:")
        for r in rows[:5]:
            print("  ", r)
        print("[dry-run] 前5行快照预览:")
        for s in snaps[:5]:
            print("  ", s)
        return

    # ==================== 生成 SQL ====================
    sql_path = "sql/03_real_data.sql"
    lines = ["-- 真实财务数据(东财/新浪接口采集, 生成时间见下行)", "-- " + time.strftime("%Y-%m-%d %H:%M:%S")]
    lines.append("USE `财报分析系统`;")
    lines.append("SET FOREIGN_KEY_CHECKS=0;")
    lines.append("TRUNCATE TABLE `财务原始数据`;")
    lines.append("TRUNCATE TABLE `估值快照`;")
    lines.append("TRUNCATE TABLE `财务指标`;")
    lines.append("TRUNCATE TABLE `行业对标`;")
    lines.append("TRUNCATE TABLE `解读报告`;")
    lines.append("SET FOREIGN_KEY_CHECKS=1;")
    lines.append("INSERT INTO `财务原始数据` (`公司ID`,`财年`,`报告期`,`项目ID`,`金额`,`数据来源`) VALUES")
    lines.append(",\n".join("({}, {}, '{}', {}, {}, '东方财富接口')".format(
        cid, year, REPORT_PERIOD, item_id, amount) for cid, year, item_id, amount in rows) + ";")
    if snaps:
        lines.append("INSERT INTO `估值快照` (`公司ID`,`快照日期`,`收盘价`,`总市值`) VALUES")
        lines.append(",\n".join("({}, '{}', {}, {})".format(*s) for s in snaps) + ";")
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n已生成:", sql_path)

    if args.db:
        try:
            import pymysql
        except ImportError:
            print("未安装 pymysql, 跳过直写(可执行: py -3 -m pip install pymysql)")
            return
        conn = pymysql.connect(host="127.0.0.1", user="root", password=input("MySQL密码: "),
                               database="财报分析系统", charset="utf8mb4")
        cur = conn.cursor()
        for cid, year, item_id, amount in rows:
            cur.execute("INSERT INTO `财务原始数据` (`公司ID`,`财年`,`报告期`,`项目ID`,`金额`,`数据来源`) "
                        "VALUES (%s,%s,'%s',%s,%s,'东方财富接口')" % (cid, year, REPORT_PERIOD, item_id, amount))
        for s in snaps:
            cur.execute("INSERT INTO `估值快照` (`公司ID`,`快照日期`,`收盘价`,`总市值`) VALUES (%s,%s,%s,%s)", s)
        conn.commit()
        conn.close()
        print("已直写MySQL, 请执行 recalc 重算指标与对标")


def year_end_close(klines, year):
    """该年最后一个交易日的收盘价; klines 为 None 或缺失返回 None"""
    if not klines:
        return None
    dates = sorted(d for d in klines if d.startswith(str(year)))
    if not dates:
        return None
    return klines[dates[-1]]


if __name__ == "__main__":
    main()

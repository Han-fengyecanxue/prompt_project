# -*- coding: utf-8 -*-
"""
种子数据生成器: 基于Prompt工程的上市公司财报解读与行业对标系统
生成 sql/02_seed_data.sql (数据为量级近似的模拟数据, 用于系统演示与验证)
用法: py -3 sql/gen_seed.py
"""
import random
import os

random.seed(20260814)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_seed_data.sql")

# ================= 行业 =================
INDUSTRIES = [
    (1, "C39", "计算机、通信和其他电子设备制造业"),
    (2, "C27", "医药制造业"),
    (3, "C15", "酒、饮料和精制茶制造业"),
]

# ================= 公司基础画像 =================
# 字段: industry, code, name, full, exch, list_date, shares(亿股), mcap24(亿), mcap25(亿),
#       rev25(亿), growth[22,23,24,25], npm(5年,%), gm(5年,%), alr(5年,%), roe(5年,%), cur(5年),
#       cash_ratio, inv_ratio, ar_ratio, cfq(5年), capex_ratio
COMPANIES = [
    # ---------- C39 计算机、通信和其他电子设备制造业 ----------
    dict(ind=1, code="300308", name="中际旭创", full="中际旭创股份有限公司", exch="SZ", list_date="2012-04-10",
         shares=11.2, mcap24=1500, mcap25=2400,
         rev25=420, growth=[0.25, 0.45, 1.10, 0.95], npm=[11.4, 14.0, 17.5, 23.5, 28.2], gm=[26.3, 28.5, 30.5, 35.0, 42.6],
         alr=[30.0, 32.0, 35.0, 32.0, 30.2], roe=[10.0, 13.0, 18.0, 33.0, 43.8], cur=[2.2, 2.0, 1.8, 1.9, 2.0],
         cash_ratio=0.22, inv_ratio=0.16, ar_ratio=0.14, cfq=[1.1, 1.0, 1.05, 1.15, 1.10], capex=0.09),
    dict(ind=1, code="300502", name="新易盛", full="成都新易盛通信技术股份有限公司", exch="SZ", list_date="2016-03-03",
         shares=7.1, mcap24=500, mcap25=900,
         rev25=180, growth=[0.30, 0.35, 0.90, 0.85], npm=[12.0, 15.0, 18.0, 24.0, 28.0], gm=[28.0, 30.0, 32.0, 36.0, 40.0],
         alr=[28.0, 30.0, 33.0, 30.0, 28.0], roe=[11.0, 15.0, 20.0, 30.0, 38.0], cur=[2.4, 2.2, 2.0, 2.1, 2.2],
         cash_ratio=0.20, inv_ratio=0.15, ar_ratio=0.16, cfq=[1.0, 1.0, 1.0, 1.1, 1.05], capex=0.08),
    dict(ind=1, code="300394", name="天孚通信", full="苏州天孚光通信股份有限公司", exch="SZ", list_date="2015-02-17",
         shares=5.5, mcap24=450, mcap25=700,
         rev25=85, growth=[0.18, 0.25, 0.60, 0.75], npm=[22.0, 24.0, 26.0, 30.0, 33.0], gm=[45.0, 47.0, 48.0, 50.0, 52.0],
         alr=[22.0, 24.0, 26.0, 24.0, 22.0], roe=[14.0, 17.0, 22.0, 30.0, 36.0], cur=[2.8, 2.6, 2.4, 2.5, 2.6],
         cash_ratio=0.18, inv_ratio=0.10, ar_ratio=0.12, cfq=[0.95, 1.0, 1.05, 1.1, 1.05], capex=0.07),
    dict(ind=1, code="002475", name="立讯精密", full="立讯精密工业股份有限公司", exch="SZ", list_date="2010-09-15",
         shares=72.4, mcap24=2500, mcap25=3400,
         rev25=3100, growth=[0.25, 0.20, 0.15, 0.18], npm=[5.0, 5.2, 5.4, 5.6, 5.8], gm=[12.0, 12.5, 12.8, 13.0, 13.2],
         alr=[62.0, 63.0, 60.0, 58.0, 56.0], roe=[20.0, 21.0, 22.0, 22.5, 23.0], cur=[1.2, 1.2, 1.3, 1.3, 1.35],
         cash_ratio=0.12, inv_ratio=0.18, ar_ratio=0.12, cfq=[1.0, 1.05, 1.1, 1.05, 1.1], capex=0.06),
    dict(ind=1, code="601138", name="工业富联", full="富士康工业互联网股份有限公司", exch="SH", list_date="2018-06-08",
         shares=198.6, mcap24=4200, mcap25=6200,
         rev25=6800, growth=[0.12, 0.08, 0.06, 0.30], npm=[3.6, 3.8, 4.0, 4.2, 4.6], gm=[7.8, 8.0, 8.2, 8.4, 8.8],
         alr=[58.0, 57.0, 56.0, 55.0, 54.0], roe=[15.0, 16.0, 16.5, 17.0, 18.0], cur=[1.3, 1.3, 1.35, 1.4, 1.4],
         cash_ratio=0.14, inv_ratio=0.16, ar_ratio=0.12, cfq=[1.1, 1.0, 1.05, 1.0, 1.05], capex=0.04),
    dict(ind=1, code="002463", name="沪电股份", full="沪士电子股份有限公司", exch="SZ", list_date="2010-08-18",
         shares=19.1, mcap24=600, mcap25=900,
         rev25=150, growth=[0.15, 0.18, 0.25, 0.40], npm=[10.0, 11.0, 12.5, 15.0, 18.0], gm=[24.0, 25.0, 26.0, 28.0, 30.0],
         alr=[45.0, 46.0, 44.0, 42.0, 40.0], roe=[14.0, 16.0, 19.0, 24.0, 28.0], cur=[1.6, 1.6, 1.7, 1.7, 1.8],
         cash_ratio=0.15, inv_ratio=0.10, ar_ratio=0.15, cfq=[1.0, 1.05, 1.1, 1.0, 1.05], capex=0.07),
    dict(ind=1, code="002916", name="深南电路", full="深南电路股份有限公司", exch="SZ", list_date="2017-12-13",
         shares=5.1, mcap24=500, mcap25=800,
         rev25=180, growth=[0.12, 0.10, 0.15, 0.25], npm=[8.0, 9.0, 10.0, 11.5, 13.0], gm=[22.0, 23.0, 24.0, 25.0, 26.0],
         alr=[50.0, 50.0, 48.0, 46.0, 45.0], roe=[11.0, 12.5, 14.0, 16.0, 18.0], cur=[1.4, 1.4, 1.5, 1.5, 1.55],
         cash_ratio=0.12, inv_ratio=0.12, ar_ratio=0.16, cfq=[1.0, 1.0, 1.05, 1.0, 1.05], capex=0.08),
    dict(ind=1, code="600183", name="生益科技", full="广东生益科技股份有限公司", exch="SH", list_date="1998-10-28",
         shares=24.0, mcap24=450, mcap25=700,
         rev25=190, growth=[0.10, 0.12, 0.10, 0.22], npm=[8.5, 9.0, 9.5, 11.0, 12.5], gm=[23.0, 24.0, 24.5, 25.5, 26.5],
         alr=[40.0, 41.0, 40.0, 38.0, 37.0], roe=[12.0, 13.0, 14.0, 16.5, 18.5], cur=[1.8, 1.8, 1.9, 1.9, 2.0],
         cash_ratio=0.16, inv_ratio=0.11, ar_ratio=0.14, cfq=[1.05, 1.0, 1.05, 1.1, 1.05], capex=0.06),
    # ---------- C27 医药制造业 ----------
    dict(ind=2, code="600276", name="恒瑞医药", full="江苏恒瑞医药股份有限公司", exch="SH", list_date="2000-10-18",
         shares=63.8, mcap24=2800, mcap25=3300,
         rev25=280, growth=[-0.06, -0.02, 0.05, 0.12], npm=[16.0, 14.5, 15.0, 17.0, 19.0], gm=[84.0, 84.5, 85.0, 85.5, 86.0],
         alr=[12.0, 12.0, 11.0, 10.5, 10.0], roe=[12.0, 10.5, 11.0, 14.0, 17.0], cur=[4.0, 4.2, 4.5, 4.6, 4.8],
         cash_ratio=0.35, inv_ratio=0.06, ar_ratio=0.10, cfq=[0.9, 0.95, 1.0, 1.05, 1.1], capex=0.05),
    dict(ind=2, code="603259", name="药明康德", full="无锡药明康德新药开发股份有限公司", exch="SH", list_date="2018-05-08",
         shares=29.2, mcap24=1800, mcap25=2200,
         rev25=420, growth=[0.30, 0.25, 0.12, 0.08], npm=[18.0, 19.0, 20.0, 18.0, 17.0], gm=[36.0, 37.0, 38.0, 39.0, 40.0],
         alr=[30.0, 32.0, 34.0, 33.0, 32.0], roe=[18.0, 19.0, 20.0, 17.0, 15.0], cur=[2.2, 2.0, 1.9, 1.9, 2.0],
         cash_ratio=0.15, inv_ratio=0.05, ar_ratio=0.13, cfq=[0.95, 1.0, 1.05, 1.0, 1.05], capex=0.07),
    dict(ind=2, code="300760", name="迈瑞医疗", full="深圳迈瑞生物医疗电子股份有限公司", exch="SZ", list_date="2018-10-16",
         shares=12.1, mcap24=3000, mcap25=3100,
         rev25=380, growth=[0.20, 0.18, 0.12, 0.10], npm=[28.0, 29.0, 30.0, 30.5, 31.0], gm=[64.0, 64.5, 65.0, 65.5, 66.0],
         alr=[28.0, 28.0, 29.0, 30.0, 30.0], roe=[30.0, 31.0, 32.0, 31.0, 30.0], cur=[2.0, 2.0, 2.1, 2.1, 2.2],
         cash_ratio=0.25, inv_ratio=0.10, ar_ratio=0.12, cfq=[1.0, 1.05, 1.05, 1.1, 1.1], capex=0.05),
    dict(ind=2, code="600436", name="片仔癀", full="漳州片仔癀药业股份有限公司", exch="SH", list_date="2003-06-16",
         shares=6.0, mcap24=1300, mcap25=1300,
         rev25=100, growth=[0.12, 0.10, 0.12, 0.08], npm=[25.0, 26.0, 27.0, 28.0, 28.5], gm=[45.0, 45.5, 46.0, 46.5, 47.0],
         alr=[18.0, 18.0, 17.0, 17.0, 16.5], roe=[22.0, 23.0, 24.0, 24.5, 25.0], cur=[4.5, 4.6, 4.8, 4.9, 5.0],
         cash_ratio=0.30, inv_ratio=0.15, ar_ratio=0.06, cfq=[0.9, 0.95, 1.0, 1.0, 1.05], capex=0.03),
    dict(ind=2, code="000538", name="云南白药", full="云南白药集团股份有限公司", exch="SZ", list_date="1993-12-15",
         shares=17.8, mcap24=900, mcap25=1000,
         rev25=400, growth=[0.08, 0.06, 0.05, 0.06], npm=[8.0, 9.0, 10.0, 10.5, 11.0], gm=[26.0, 26.5, 27.0, 27.5, 28.0],
         alr=[25.0, 25.0, 24.0, 24.0, 23.0], roe=[10.0, 11.0, 12.0, 12.5, 13.0], cur=[3.0, 3.1, 3.2, 3.3, 3.4],
         cash_ratio=0.25, inv_ratio=0.12, ar_ratio=0.10, cfq=[0.95, 1.0, 1.05, 1.0, 1.05], capex=0.03),
    dict(ind=2, code="600196", name="复星医药", full="上海复星医药(集团)股份有限公司", exch="SH", list_date="1998-08-07",
         shares=26.7, mcap24=600, mcap25=700,
         rev25=430, growth=[0.12, 0.08, 0.05, 0.04], npm=[8.0, 7.5, 7.0, 7.5, 8.0], gm=[45.0, 45.5, 46.0, 46.5, 47.0],
         alr=[45.0, 46.0, 47.0, 46.0, 45.0], roe=[8.0, 7.5, 7.0, 7.5, 8.0], cur=[1.5, 1.5, 1.4, 1.45, 1.5],
         cash_ratio=0.12, inv_ratio=0.08, ar_ratio=0.12, cfq=[0.85, 0.9, 0.95, 0.9, 0.95], capex=0.05),
    dict(ind=2, code="300122", name="智飞生物", full="重庆智飞生物制品股份有限公司", exch="SZ", list_date="2010-09-28",
         shares=24.0, mcap24=700, mcap25=600,
         rev25=320, growth=[0.25, 0.15, 0.05, -0.10], npm=[20.0, 18.0, 15.0, 12.0, 10.0], gm=[42.0, 40.0, 38.0, 36.0, 34.0],
         alr=[35.0, 36.0, 37.0, 36.0, 35.0], roe=[28.0, 22.0, 16.0, 11.0, 8.0], cur=[2.0, 2.0, 2.1, 2.1, 2.2],
         cash_ratio=0.18, inv_ratio=0.10, ar_ratio=0.12, cfq=[1.0, 0.95, 0.9, 0.85, 0.9], capex=0.04),
    dict(ind=2, code="000661", name="长春高新", full="长春高新技术产业(集团)股份有限公司", exch="SZ", list_date="1996-12-18",
         shares=4.0, mcap24=500, mcap25=400,
         rev25=130, growth=[0.15, 0.10, 0.05, 0.02], npm=[28.0, 26.0, 24.0, 22.0, 20.0], gm=[85.0, 84.0, 83.0, 82.0, 81.0],
         alr=[30.0, 31.0, 32.0, 31.0, 30.0], roe=[25.0, 22.0, 18.0, 15.0, 12.0], cur=[2.2, 2.2, 2.3, 2.3, 2.4],
         cash_ratio=0.20, inv_ratio=0.08, ar_ratio=0.14, cfq=[1.0, 1.0, 0.95, 0.95, 0.9], capex=0.04),
    # ---------- C15 酒、饮料和精制茶制造业 ----------
    dict(ind=3, code="600519", name="贵州茅台", full="贵州茅台酒股份有限公司", exch="SH", list_date="2001-08-27",
         shares=12.6, mcap24=21000, mcap25=18000,
         rev25=1750, growth=[0.12, 0.16, 0.17, 0.15], npm=[47.0, 48.0, 49.0, 50.0, 51.0], gm=[91.0, 91.5, 91.8, 92.0, 92.2],
         alr=[21.0, 20.0, 19.0, 19.0, 18.5], roe=[30.0, 31.0, 32.0, 33.0, 34.0], cur=[3.8, 4.0, 4.2, 4.3, 4.5],
         cash_ratio=0.55, inv_ratio=0.10, ar_ratio=0.02, cfq=[1.1, 1.05, 1.1, 1.15, 1.1], capex=0.04),
    dict(ind=3, code="000858", name="五粮液", full="宜宾五粮液股份有限公司", exch="SZ", list_date="1998-04-27",
         shares=38.8, mcap24=5200, mcap25=5000,
         rev25=920, growth=[0.12, 0.12, 0.10, 0.08], npm=[35.0, 36.0, 37.0, 37.5, 38.0], gm=[74.0, 75.0, 76.0, 76.5, 77.0],
         alr=[26.0, 25.0, 24.0, 23.5, 23.0], roe=[24.0, 25.0, 26.0, 26.5, 27.0], cur=[3.0, 3.2, 3.4, 3.5, 3.6],
         cash_ratio=0.45, inv_ratio=0.14, ar_ratio=0.02, cfq=[1.0, 1.05, 1.1, 1.05, 1.1], capex=0.03),
    dict(ind=3, code="000568", name="泸州老窖", full="泸州老窖股份有限公司", exch="SZ", list_date="1994-05-09",
         shares=14.7, mcap24=2200, mcap25=2000,
         rev25=330, growth=[0.18, 0.20, 0.16, 0.10], npm=[38.0, 39.0, 40.0, 41.0, 42.0], gm=[82.0, 83.0, 84.0, 85.0, 86.0],
         alr=[30.0, 28.0, 27.0, 26.0, 25.0], roe=[28.0, 30.0, 31.0, 32.0, 33.0], cur=[2.8, 3.0, 3.2, 3.3, 3.4],
         cash_ratio=0.45, inv_ratio=0.16, ar_ratio=0.02, cfq=[1.0, 1.05, 1.1, 1.1, 1.05], capex=0.03),
    dict(ind=3, code="600809", name="山西汾酒", full="山西杏花村汾酒厂股份有限公司", exch="SH", list_date="1994-01-06",
         shares=12.2, mcap24=2600, mcap25=2800,
         rev25=340, growth=[0.30, 0.28, 0.20, 0.12], npm=[22.0, 24.0, 26.0, 28.0, 30.0], gm=[74.0, 75.0, 76.0, 77.0, 78.0],
         alr=[40.0, 38.0, 36.0, 35.0, 34.0], roe=[25.0, 28.0, 30.0, 32.0, 33.0], cur=[2.0, 2.2, 2.4, 2.5, 2.6],
         cash_ratio=0.35, inv_ratio=0.18, ar_ratio=0.03, cfq=[0.95, 1.0, 1.05, 1.0, 1.05], capex=0.04),
    dict(ind=3, code="002304", name="洋河股份", full="江苏洋河酒厂股份有限公司", exch="SZ", list_date="2009-11-06",
         shares=15.1, mcap24=1200, mcap25=1000,
         rev25=310, growth=[0.10, 0.08, 0.05, 0.03], npm=[30.0, 30.5, 31.0, 30.0, 29.0], gm=[72.0, 73.0, 73.5, 74.0, 74.5],
         alr=[25.0, 25.0, 24.0, 24.0, 23.0], roe=[19.0, 19.5, 20.0, 19.0, 18.0], cur=[2.5, 2.6, 2.7, 2.8, 2.9],
         cash_ratio=0.35, inv_ratio=0.18, ar_ratio=0.02, cfq=[1.0, 1.0, 1.05, 1.0, 1.0], capex=0.03),
    dict(ind=3, code="000596", name="古井贡酒", full="安徽古井贡酒股份有限公司", exch="SZ", list_date="1996-09-27",
         shares=5.3, mcap24=1200, mcap25=1200,
         rev25=250, growth=[0.25, 0.22, 0.18, 0.14], npm=[18.0, 20.0, 22.0, 24.0, 25.0], gm=[75.0, 76.0, 77.0, 78.0, 79.0],
         alr=[45.0, 43.0, 41.0, 39.0, 38.0], roe=[22.0, 25.0, 27.0, 29.0, 30.0], cur=[2.0, 2.1, 2.2, 2.3, 2.4],
         cash_ratio=0.30, inv_ratio=0.18, ar_ratio=0.03, cfq=[0.9, 0.95, 1.0, 1.0, 1.05], capex=0.04),
    dict(ind=3, code="603369", name="今世缘", full="江苏今世缘酒业股份有限公司", exch="SH", list_date="2014-07-03",
         shares=12.5, mcap24=500, mcap25=500,
         rev25=120, growth=[0.24, 0.22, 0.20, 0.15], npm=[22.0, 24.0, 26.0, 28.0, 29.0], gm=[70.0, 71.0, 72.0, 73.0, 74.0],
         alr=[35.0, 34.0, 33.0, 32.0, 31.0], roe=[20.0, 22.0, 24.0, 26.0, 27.0], cur=[2.0, 2.1, 2.2, 2.3, 2.4],
         cash_ratio=0.30, inv_ratio=0.15, ar_ratio=0.03, cfq=[0.95, 1.0, 1.05, 1.05, 1.0], capex=0.04),
    dict(ind=3, code="600600", name="青岛啤酒", full="青岛啤酒股份有限公司", exch="SH", list_date="1993-08-27",
         shares=13.6, mcap24=900, mcap25=1000,
         rev25=340, growth=[0.06, 0.05, 0.04, 0.03], npm=[8.0, 9.0, 10.0, 11.0, 12.0], gm=[38.0, 39.0, 40.0, 40.5, 41.0],
         alr=[45.0, 44.0, 43.0, 42.0, 41.0], roe=[12.0, 14.0, 15.0, 16.0, 17.0], cur=[1.6, 1.6, 1.7, 1.7, 1.8],
         cash_ratio=0.20, inv_ratio=0.10, ar_ratio=0.05, cfq=[1.2, 1.2, 1.25, 1.25, 1.3], capex=0.05),
]

YEARS = [2021, 2022, 2023, 2024, 2025]

# 报表项目: (id, code, name, report_type, unit, order)
ITEMS = [
    (1, "operating_revenue", "营业收入", "利润表", "元", 1),
    (2, "operating_cost", "营业成本", "利润表", "元", 2),
    (3, "gross_profit", "营业利润", "利润表", "元", 5),
    (4, "net_profit", "净利润", "利润表", "元", 10),
    (5, "net_profit_parent", "归属于上市公司股东的净利润", "利润表", "元", 11),
    (6, "net_profit_parent_deducted", "扣除非经常性损益的净利润", "利润表", "元", 12),
    (7, "eps_basic", "基本每股收益", "利润表", "元/股", 20),
    (8, "monetary_funds", "货币资金", "资产负债表", "元", 1),
    (9, "trading_financial_assets", "交易性金融资产", "资产负债表", "元", 2),
    (10, "notes_receivable", "应收票据", "资产负债表", "元", 5),
    (11, "accounts_receivable", "应收账款", "资产负债表", "元", 6),
    (12, "inventory", "存货", "资产负债表", "元", 10),
    (13, "total_assets", "总资产", "资产负债表", "元", 50),
    (14, "short_term_borrowings", "短期借款", "资产负债表", "元", 60),
    (15, "accounts_payable", "应付账款", "资产负债表", "元", 65),
    (16, "total_liabilities", "总负债", "资产负债表", "元", 90),
    (17, "total_equity", "股东权益合计", "资产负债表", "元", 95),
    (18, "operating_cashflow", "经营活动现金流量净额", "现金流量表", "元", 10),
    (19, "investing_cashflow", "投资活动现金流量净额", "现金流量表", "元", 20),
    (20, "financing_cashflow", "筹资活动现金流量净额", "现金流量表", "元", 30),
    (21, "current_assets_total", "流动资产合计", "资产负债表", "元", 40),
    (22, "current_liabilities_total", "流动负债合计", "资产负债表", "元", 85),
]

# 提示词模板(三层Prompt工程)
PROMPT_TEMPLATES = [
    (1, "角色设定",
     "你是一位资深的上司公司财务分析师，拥有 CFA 资质与 10 年以上 A 股财报分析经验，"
     "擅长通过财务指标对上市公司进行客观诊断，并以通俗易懂的语言向普通投资者解释专业结论。"
     "你的分析风格：客观、严谨、克制，不夸大、不唱多、不唱空，结论必须有数据支撑。",
     "1.0", 1),
    (2, "数据注入",
     "以下是由系统精确计算出的【该公司】{fiscalYear}年财务指标与行业对标数据（JSON 格式），"
     "这是本次分析唯一可信的数据来源：\n{data_json}\n"
     "行业对标口径：行业均值/中位数/P25/P75 基于同行业上市公司同一年度数据计算；"
     "百分位排名表示该公司指标值在行业内所处位置（0-100，越高表示相对越优）。",
     "1.0", 1),
    (3, "输出约束",
     "请严格按照以下要求输出解读报告：\n"
     "1. 只能使用【数据注入】中提供的数据，严禁编造、推断或补充任何数据注入中不存在的数字；\n"
     "2. 报告结构固定为：一、公司概览；二、盈利能力分析；三、成长性分析；四、财务风险分析；"
     "五、估值水平分析；六、综合结论与风险提示；\n"
     "3. 每个章节必须引用具体指标数值与行业对标结果（如：ROE 为 25.3%，高于行业中位数 18.2%）；\n"
     "4. 结论部分给出综合评级（优秀/良好/一般/偏弱）与理由；\n"
     "5. 使用中文、Markdown 格式，控制在 800 字以内；\n"
     "6. 如果某维度数据缺失，明确说明“该维度数据不足，无法分析”，不得猜测。",
     "1.0", 1),
]


def money(yi):
    """亿元 -> 元"""
    return round(yi * 1e8, 2)


def build_financials(c):
    """根据公司画像生成 2021-2025 每年 22 个报表项目金额(元)。"""
    out = {}
    rev = [None] * 5
    # 从 2025 倒推 2021 营收
    rev[4] = c["rev25"]
    for i in range(3, -1, -1):
        rev[i] = rev[i + 1] / (1 + c["growth"][i])
    for t, year in enumerate(YEARS):
        np_p = rev[t] * c["npm"][t] / 100.0
        minority = random.uniform(0.02, 0.06)
        np = np_p * (1 + minority)
        gp = np * random.uniform(1.12, 1.22)          # 营业利润
        deducted = np_p * random.uniform(0.90, 0.97)   # 扣非归母
        eps = np_p / c["shares"]
        equity = np_p / (c["roe"][t] / 100.0)
        ta = equity / (1 - c["alr"][t] / 100.0)
        tl = ta - equity
        cash_a = ta * c["cash_ratio"]
        inv = ta * c["inv_ratio"]
        ar = ta * c["ar_ratio"]
        notes = ar * 0.25
        ars = ar * 0.75
        cur_a = cash_a + inv + ar          # 流动资产合计
        cur_l = cur_a / c["cur"][t]        # 流动负债合计
        if cur_l > tl:                     # 保证不超总负债
            cur_l = tl * 0.9
        non_cur_l = tl - cur_l
        st_loan = cur_l * 0.35
        ap = cur_l * 0.40
        tfa = cash_a * 0.30
        mf = cash_a * 0.70
        op_cf = np * c["cfq"][t]
        inv_cf = -(ta * c["capex"])
        fin_cf = -(np * random.uniform(0.25, 0.45))   # 分红/偿债为主
        vals = {
            "operating_revenue": rev[t],
            "operating_cost": rev[t] * (1 - c["gm"][t] / 100.0),
            "gross_profit": gp,
            "net_profit": np,
            "net_profit_parent": np_p,
            "net_profit_parent_deducted": deducted,
            "eps_basic": eps,          # 元/股, 不放大
            "monetary_funds": mf,
            "trading_financial_assets": tfa,
            "notes_receivable": notes,
            "accounts_receivable": ars,
            "inventory": inv,
            "total_assets": ta,
            "short_term_borrowings": st_loan,
            "accounts_payable": ap,
            "total_liabilities": tl,
            "total_equity": equity,
            "operating_cashflow": op_cf,
            "investing_cashflow": inv_cf,
            "financing_cashflow": fin_cf,
            "current_assets_total": cur_a,
            "current_liabilities_total": cur_l,
        }
        # 金额统一换算: 亿元 -> 元 (eps_basic 已是 元/股, 不换算)
        for k, v in vals.items():
            if k != "eps_basic":
                vals[k] = money(v)
        out[year] = vals
    return out


def main():
    lines = []
    lines.append("-- ============================================================")
    lines.append("-- 种子数据(模拟数据, 量级近似真实财报, 仅用于系统演示/验证)")
    lines.append("-- 生成器: sql/gen_seed.py (py -3 sql/gen_seed.py)")
    lines.append("-- ============================================================")
    lines.append("USE `财报分析系统`;")
    lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    lines.append("TRUNCATE TABLE `解读报告`;")
    lines.append("TRUNCATE TABLE `财务原始数据`;")
    lines.append("TRUNCATE TABLE `财务指标`;")
    lines.append("TRUNCATE TABLE `行业对标`;")
    lines.append("TRUNCATE TABLE `估值快照`;")
    lines.append("TRUNCATE TABLE `上市公司`;")
    lines.append("TRUNCATE TABLE `报表项目`;")
    lines.append("TRUNCATE TABLE `提示词模板`;")
    lines.append("TRUNCATE TABLE `行业分类`;")
    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("")

    # 行业
    lines.append("-- 行业分类")
    for iid, code, name in INDUSTRIES:
        lines.append("INSERT INTO `行业分类` (`行业ID`,`行业代码`,`行业名称`,`上级行业ID`,`层级`) VALUES (%d,'%s','%s',0,1);" % (iid, code, name))
    lines.append("")

    # 报表项目
    lines.append("-- 报表项目")
    for pid, code, name, rtype, unit, order in ITEMS:
        lines.append("INSERT INTO `报表项目` (`项目ID`,`项目编码`,`项目名称`,`所属报表`,`单位`,`显示顺序`) VALUES (%d,'%s','%s','%s','%s',%d);"
                     % (pid, code, name, rtype, unit, order))
    lines.append("")

    # 上市公司
    lines.append("-- 上市公司")
    for i, c in enumerate(COMPANIES, start=1):
        lines.append("INSERT INTO `上市公司` (`公司ID`,`股票代码`,`股票简称`,`公司全称`,`交易所`,`行业ID`,`上市日期`,`状态`) VALUES (%d,'%s','%s','%s','%s',%d,'%s',1);"
                     % (i, c["code"], c["name"], c["full"], c["exch"], c["ind"], c["list_date"]))
    lines.append("")

    # 财务原始数据
    lines.append("-- 财务原始数据(24家公司 x 5年 x 22个项目)")
    code_to_id = {code: pid for pid, code, *_ in ITEMS}
    rows = []
    for i, c in enumerate(COMPANIES, start=1):
        fin = build_financials(c)
        for t, year in enumerate(YEARS):
            for code, amount in fin[year].items():
                pid = code_to_id[code]
                rows.append("(%d,%d,'年报',%d,%.2f,'模拟数据(量级近似公开财报)')"
                            % (i, year, pid, amount))
    for r in rows:
        lines.append("INSERT INTO `财务原始数据` (`公司ID`,`财年`,`报告期`,`项目ID`,`金额`,`数据来源`) VALUES %s;" % r)
    lines.append("")

    # 估值快照
    lines.append("-- 估值快照(2024/2025年末)")
    for i, c in enumerate(COMPANIES, start=1):
        p24 = c["mcap24"] / c["shares"]
        p25 = c["mcap25"] / c["shares"]
        lines.append("INSERT INTO `估值快照` (`公司ID`,`快照日期`,`收盘价`,`总市值`) VALUES (%d,'2024-12-31',%.2f,%.2f);" % (i, p24, c["mcap24"] * 1e8))
        lines.append("INSERT INTO `估值快照` (`公司ID`,`快照日期`,`收盘价`,`总市值`) VALUES (%d,'2025-12-31',%.2f,%.2f);" % (i, p25, c["mcap25"] * 1e8))
    lines.append("")

    # 提示词模板
    lines.append("-- 提示词模板(三层Prompt工程)")
    for tid, ttype, content, ver, enabled in PROMPT_TEMPLATES:
        content_esc = content.replace("'", "''")
        lines.append("INSERT INTO `提示词模板` (`模板ID`,`模板类型`,`模板内容`,`版本号`,`是否启用`) VALUES (%d,'%s','%s','%s',%d);"
                     % (tid, ttype, content_esc, ver, enabled))
    lines.append("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("已生成:", OUT)
    print("公司数: %d, 财务原始数据行数: %d, 估值快照: %d" % (len(COMPANIES), len(rows), len(COMPANIES) * 2))


if __name__ == "__main__":
    main()

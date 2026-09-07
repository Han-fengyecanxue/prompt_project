package com.fycx.service.calc;

import com.fycx.common.IndicatorDef;
import com.fycx.entity.FinancialIndicator;
import com.fycx.entity.ValuationSnapshot;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 财务指标计算引擎
 * 输入: 某公司某年度全部报表项目(编码->金额) + 上年数据(成长性指标) + 估值快照(PE/PB)
 * 输出: 标准化财务指标列表
 * 原则: 所有数字由系统精确计算, 可溯源、可验证(双层解耦架构的底层)
 */
public class IndicatorCalcEngine {

    private static final BigDecimal HUNDRED = new BigDecimal("100");

    private IndicatorCalcEngine() {
    }

    /** 计算某公司某年度全部指标 */
    public static List<FinancialIndicator> calc(Integer companyId, Integer fiscalYear, String reportPeriod,
                                                Map<String, BigDecimal> items,
                                                Map<String, BigDecimal> priorItems,
                                                ValuationSnapshot valuation) {
        List<FinancialIndicator> result = new ArrayList<>();
        Date now = new Date();

        BigDecimal rev = items.get("operating_revenue");
        BigDecimal cost = items.get("operating_cost");
        BigDecimal np = items.get("net_profit");
        BigDecimal npParent = items.get("net_profit_parent");
        BigDecimal equity = items.get("total_equity");
        BigDecimal ta = items.get("total_assets");
        BigDecimal tl = items.get("total_liabilities");
        BigDecimal ca = items.get("current_assets_total");
        BigDecimal cl = items.get("current_liabilities_total");
        BigDecimal inv = items.get("inventory");
        BigDecimal opcf = items.get("operating_cashflow");
        BigDecimal eps = items.get("eps_basic");

        Map<String, BigDecimal> values = new HashMap<>();

        // ---- 盈利能力 ----
        // ROE = 归母净利润 / 平均股东权益
        BigDecimal equityPrior = priorItems == null ? null : priorItems.get("total_equity");
        BigDecimal avgEquity = average(equity, equityPrior);
        values.put("roe", percent(npParent, avgEquity));
        // 毛利率
        values.put("gross_margin", percent(subtract(rev, cost), rev));
        // 归母净利率
        values.put("net_margin_parent", percent(npParent, rev));

        // ---- 成长性(需上年数据) ----
        if (priorItems != null) {
            BigDecimal revPrior = priorItems.get("operating_revenue");
            BigDecimal npParentPrior = priorItems.get("net_profit_parent");
            values.put("revenue_growth", percent(subtract(rev, revPrior), abs(revPrior)));
            values.put("profit_growth", percent(subtract(npParent, npParentPrior), abs(npParentPrior)));
        }

        // ---- 财务风险 ----
        values.put("asset_liability_ratio", percent(tl, ta));
        values.put("current_ratio", divide(ca, cl));
        values.put("quick_ratio", divide(subtract(ca, inv), cl));

        // ---- 盈利质量 ----
        values.put("cashflow_quality", divide(opcf, np));

        // ---- 每股指标 ----
        values.put("eps", eps);

        // ---- 估值(需估值快照) ----
        if (valuation != null && valuation.getMarketCap() != null
                && valuation.getMarketCap().compareTo(BigDecimal.ZERO) > 0) {
            values.put("pe", divide(valuation.getMarketCap(), npParent));
            values.put("pb", divide(valuation.getMarketCap(), equity));
        }

        for (IndicatorDef def : IndicatorDef.all()) {
            BigDecimal v = values.get(def.getCode());
            if (v == null) continue;
            FinancialIndicator ind = new FinancialIndicator();
            ind.setCompanyId(companyId);
            ind.setFiscalYear(fiscalYear);
            ind.setReportPeriod(reportPeriod);
            ind.setIndicatorCode(def.getCode());
            ind.setIndicatorValue(round(v, 4));
            ind.setUnit(def.getUnit());
            ind.setCalcTime(now);
            result.add(ind);
        }
        return result;
    }

    // ================== 基础运算工具 ==================

    private static BigDecimal percent(BigDecimal num, BigDecimal den) {
        if (num == null || den == null || den.compareTo(BigDecimal.ZERO) == 0) return null;
        return num.multiply(HUNDRED).divide(den, 6, RoundingMode.HALF_UP);
    }

    private static BigDecimal divide(BigDecimal num, BigDecimal den) {
        if (num == null || den == null || den.compareTo(BigDecimal.ZERO) == 0) return null;
        return num.divide(den, 6, RoundingMode.HALF_UP);
    }

    private static BigDecimal subtract(BigDecimal a, BigDecimal b) {
        if (a == null || b == null) return null;
        return a.subtract(b);
    }

    private static BigDecimal abs(BigDecimal v) {
        return v == null ? null : v.abs();
    }

    private static BigDecimal average(BigDecimal a, BigDecimal b) {
        if (a == null) return b;
        if (b == null) return a;
        return a.add(b).divide(new BigDecimal("2"), 6, RoundingMode.HALF_UP);
    }

    public static BigDecimal round(BigDecimal v, int scale) {
        if (v == null) return null;
        return v.setScale(scale, RoundingMode.HALF_UP);
    }
}

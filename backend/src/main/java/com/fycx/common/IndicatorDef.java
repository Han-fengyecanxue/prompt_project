package com.fycx.common;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 财务指标元数据定义(指标编码/名称/维度/单位/方向)
 * 方向: higher_better-越高越好(排名1为最大) lower_better-越低越好(排名1为最小, 如资产负债率/PE/PB)
 */
public enum IndicatorDef {

    ROE("roe", "净资产收益率(ROE)", "盈利能力", "%", "higher_better", "净资产收益率", "净资产收益", "ROE"),
    GROSS_MARGIN("gross_margin", "毛利率", "盈利能力", "%", "higher_better", "毛利率", "毛利"),
    NET_MARGIN_PARENT("net_margin_parent", "归母净利率", "盈利能力", "%", "higher_better", "归母净利率", "净利率"),
    REVENUE_GROWTH("revenue_growth", "营业收入增长率", "成长性", "%", "higher_better", "营收增长率", "营业收入增长率", "营收增长", "收入增长"),
    PROFIT_GROWTH("profit_growth", "归母净利润增长率", "成长性", "%", "higher_better", "利润增长率", "净利增长", "利润增长"),
    ASSET_LIABILITY_RATIO("asset_liability_ratio", "资产负债率", "财务风险", "%", "lower_better", "资产负债率", "负债率"),
    CURRENT_RATIO("current_ratio", "流动比率", "财务风险", "倍", "higher_better", "流动比率", "流动"),
    QUICK_RATIO("quick_ratio", "速动比率", "财务风险", "倍", "higher_better", "速动比率", "速动"),
    CASHFLOW_QUALITY("cashflow_quality", "经营现金流/净利润", "盈利质量", "倍", "higher_better", "经营现金流", "现金流", "现金含量"),
    EPS("eps", "基本每股收益", "每股指标", "元/股", "higher_better", "每股收益", "EPS", "eps"),
    PE("pe", "市盈率PE", "估值", "倍", "lower_better", "市盈率", "PE", "pe"),
    PB("pb", "市净率PB", "估值", "倍", "lower_better", "市净率", "PB", "pb");

    private final String code;
    private final String name;
    private final String dimension;
    private final String unit;
    private final String betterDirection;
    private final String[] aliases;

    IndicatorDef(String code, String name, String dimension, String unit, String betterDirection, String... aliases) {
        this.code = code;
        this.name = name;
        this.dimension = dimension;
        this.unit = unit;
        this.betterDirection = betterDirection;
        this.aliases = aliases;
    }

    public String getCode() { return code; }
    public String getName() { return name; }
    public String getDimension() { return dimension; }
    public String getUnit() { return unit; }
    public String getBetterDirection() { return betterDirection; }
    public String[] getAliases() { return aliases; }

    public static IndicatorDef fromCode(String code) {
        for (IndicatorDef def : values()) {
            if (def.code.equals(code)) return def;
        }
        return null;
    }

    public static List<IndicatorDef> all() {
        return Arrays.asList(values());
    }

    /** 已知的指标编码集合 */
    public static List<String> allCodes() {
        return Arrays.stream(values()).map(IndicatorDef::getCode).collect(Collectors.toList());
    }
}

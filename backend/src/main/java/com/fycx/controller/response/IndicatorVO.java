package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 财务指标(含元数据)
 */
@Data
public class IndicatorVO {
    private String indicatorCode;
    private String indicatorName;
    private String dimension;        // 盈利能力/成长性/财务风险/盈利质量/估值/每股指标
    private String unit;
    private BigDecimal value;
    private String betterDirection;  // higher_better / lower_better
}

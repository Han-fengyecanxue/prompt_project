package com.fycx.controller.request;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 交叉筛选条件
 * operator: gt(大于) gte(大于等于) lt(小于) lte(小于等于) between(区间) pct_gt(行业百分位高于) pct_lt(行业百分位低于)
 */
@Data
public class ScreeningCondition {
    private String indicatorCode;
    private String operator;
    private BigDecimal value;
    private BigDecimal value2;
}

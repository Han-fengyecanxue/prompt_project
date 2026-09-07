package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 筛选条件判定明细
 */
@Data
public class ScreeningDetailVO {
    private String indicatorCode;
    private String indicatorName;
    private String operator;         // gt/gte/lt/lte/between/pct_gt/pct_lt
    private BigDecimal value;
    private BigDecimal value2;
    private BigDecimal actualValue;  // 公司实际指标值
    private Boolean passed;
}

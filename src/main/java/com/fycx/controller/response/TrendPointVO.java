package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 趋势数据点
 */
@Data
public class TrendPointVO {
    private Integer year;
    private BigDecimal value;
}

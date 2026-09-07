package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

/**
 * 多年度指标趋势
 */
@Data
public class TrendVO {
    private String indicatorCode;
    private String indicatorName;
    private String unit;
    private List<TrendPointVO> points;
}

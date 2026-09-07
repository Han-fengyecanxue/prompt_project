package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;

/**
 * 行业指标排名项
 */
@Data
public class RankingItemVO {
    private Integer companyId;
    private String stockCode;
    private String stockName;
    private BigDecimal value;
    private BigDecimal percentile;   // 原始百分位
    private Integer rank;            // 排名(1=最优)
}

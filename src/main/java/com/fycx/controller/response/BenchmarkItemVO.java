package com.fycx.controller.response;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

/**
 * 行业对标-单指标结果
 */
@Data
public class BenchmarkItemVO {
    private String indicatorCode;
    private String indicatorName;
    private String dimension;
    private String unit;
    private String betterDirection;

    private BigDecimal companyValue;   // 公司值
    private BigDecimal avgValue;       // 行业均值
    private BigDecimal medianValue;    // 行业中位数
    private BigDecimal p25;
    private BigDecimal p75;
    private BigDecimal stdDev;
    private Integer companyCount;      // 行业样本数

    private BigDecimal percentile;     // 原始百分位(0-100, 值越小表示数值越低)
    private BigDecimal score;          // 方向调整后的评分(0-100, 越高越优)
    private Integer rank;              // 行业排名(1=最优)
    private Integer total;             // 行业公司总数
}

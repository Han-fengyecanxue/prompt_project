package com.fycx.controller.request;

import lombok.Data;

import java.util.List;

/**
 * 多条件交叉筛选请求
 */
@Data
public class ScreeningRequest {
    private Integer industryId;                       // 可选, 不传则全市场
    private Integer fiscalYear;
    private String reportPeriod = "年报";
    private List<ScreeningCondition> conditions;      // 条件之间为 AND 关系
    private Integer page = 1;
    private Integer size = 50;
}

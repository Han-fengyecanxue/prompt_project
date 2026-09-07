package com.fycx.controller.request;

import lombok.Data;

/**
 * 财务查询请求(公司 + 年度)
 */
@Data
public class FinanceYearRequest {
    private Integer companyId;
    private Integer fiscalYear;
    private String reportPeriod = "年报";
}

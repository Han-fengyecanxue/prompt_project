package com.fycx.controller.response;

import lombok.Data;

/**
 * 公司信息(含行业名称)
 */
@Data
public class CompanyVO {
    private Integer companyId;
    private String stockCode;
    private String stockName;
    private String fullName;
    private String exchange;
    private Integer industryId;
    private String industryName;
    private String listDate;
    private Integer status;
}

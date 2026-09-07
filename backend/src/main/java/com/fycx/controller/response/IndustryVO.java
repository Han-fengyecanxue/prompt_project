package com.fycx.controller.response;

import lombok.Data;

/**
 * 行业(含公司数量)
 */
@Data
public class IndustryVO {
    private Integer industryId;
    private String industryCode;
    private String industryName;
    private Integer companyCount;
}

package com.fycx.controller.response;

import lombok.Data;

import java.util.List;

/**
 * 行业对标: 某公司某年度在所属行业的全部指标对标结果
 */
@Data
public class BenchmarkVO {
    private CompanyVO company;
    private Integer fiscalYear;
    private String reportPeriod;
    private String industryName;
    private List<BenchmarkItemVO> items;
}

package com.fycx.controller.response;

import lombok.Data;

import java.util.List;

/**
 * 财务画像: 某公司某年度 原始数据 + 指标 + 估值
 */
@Data
public class ProfileVO {
    private CompanyVO company;
    private Integer fiscalYear;
    private String reportPeriod;
    private String industryName;
    private List<RawItemVO> items;
    private List<IndicatorVO> indicators;
    private ValuationVO valuation;
}

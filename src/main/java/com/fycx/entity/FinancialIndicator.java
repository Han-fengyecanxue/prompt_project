package com.fycx.entity;

import java.math.BigDecimal;
import java.util.Date;

public class FinancialIndicator {
    private Long indicatorId;

    private Integer companyId;

    private Integer fiscalYear;

    private String reportPeriod;

    private String indicatorCode;

    private BigDecimal indicatorValue;

    private String unit;

    private Date calcTime;

    public Long getIndicatorId() {
        return indicatorId;
    }

    public void setIndicatorId(Long indicatorId) {
        this.indicatorId = indicatorId;
    }

    public Integer getCompanyId() {
        return companyId;
    }

    public void setCompanyId(Integer companyId) {
        this.companyId = companyId;
    }

    public Integer getFiscalYear() {
        return fiscalYear;
    }

    public void setFiscalYear(Integer fiscalYear) {
        this.fiscalYear = fiscalYear;
    }

    public String getReportPeriod() {
        return reportPeriod;
    }

    public void setReportPeriod(String reportPeriod) {
        this.reportPeriod = reportPeriod == null ? null : reportPeriod.trim();
    }

    public String getIndicatorCode() {
        return indicatorCode;
    }

    public void setIndicatorCode(String indicatorCode) {
        this.indicatorCode = indicatorCode == null ? null : indicatorCode.trim();
    }

    public BigDecimal getIndicatorValue() {
        return indicatorValue;
    }

    public void setIndicatorValue(BigDecimal indicatorValue) {
        this.indicatorValue = indicatorValue;
    }

    public String getUnit() {
        return unit;
    }

    public void setUnit(String unit) {
        this.unit = unit == null ? null : unit.trim();
    }

    public Date getCalcTime() {
        return calcTime;
    }

    public void setCalcTime(Date calcTime) {
        this.calcTime = calcTime;
    }
}
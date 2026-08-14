package com.fycx.entity;

import java.math.BigDecimal;

public class IndustryBenchmark {
    private Long benchmarkId;

    private Integer industryId;

    private Integer fiscalYear;

    private String reportPeriod;

    private String indicatorCode;

    private BigDecimal avgValue;

    private BigDecimal medianValue;

    private BigDecimal stdDev;

    private BigDecimal p25;

    private BigDecimal p75;

    private Integer companyCount;

    public Long getBenchmarkId() {
        return benchmarkId;
    }

    public void setBenchmarkId(Long benchmarkId) {
        this.benchmarkId = benchmarkId;
    }

    public Integer getIndustryId() {
        return industryId;
    }

    public void setIndustryId(Integer industryId) {
        this.industryId = industryId;
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

    public BigDecimal getAvgValue() {
        return avgValue;
    }

    public void setAvgValue(BigDecimal avgValue) {
        this.avgValue = avgValue;
    }

    public BigDecimal getMedianValue() {
        return medianValue;
    }

    public void setMedianValue(BigDecimal medianValue) {
        this.medianValue = medianValue;
    }

    public BigDecimal getStdDev() {
        return stdDev;
    }

    public void setStdDev(BigDecimal stdDev) {
        this.stdDev = stdDev;
    }

    public BigDecimal getP25() {
        return p25;
    }

    public void setP25(BigDecimal p25) {
        this.p25 = p25;
    }

    public BigDecimal getP75() {
        return p75;
    }

    public void setP75(BigDecimal p75) {
        this.p75 = p75;
    }

    public Integer getCompanyCount() {
        return companyCount;
    }

    public void setCompanyCount(Integer companyCount) {
        this.companyCount = companyCount;
    }
}
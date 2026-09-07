package com.fycx.service;

import com.fycx.controller.request.CompanyQueryRequest;
import com.fycx.controller.request.ScreeningRequest;
import com.fycx.controller.response.*;

import java.util.List;
import java.util.Map;

/**
 * 财务数据服务: 查询/画像/对标/排名/交叉筛选/指标重算
 */
public interface FinanceService {

    /** 行业列表(含公司数) */
    List<IndustryVO> listIndustries();

    /** 公司分页查询 */
    PageResult<CompanyVO> pageCompanies(CompanyQueryRequest req);

    /** 公司详情 */
    CompanyVO getCompany(Integer companyId);

    /** 财务画像: 原始数据 + 指标 + 估值 */
    ProfileVO getProfile(Integer companyId, Integer fiscalYear, String reportPeriod);

    /** 多年度指标趋势 */
    List<TrendVO> getTrend(Integer companyId, List<String> indicators, Integer startYear, Integer endYear);

    /** 行业对标(公司 vs 行业基准 + 百分位 + 排名) */
    BenchmarkVO getBenchmark(Integer companyId, Integer fiscalYear, String reportPeriod);

    /** 行业指标排名 */
    List<RankingItemVO> getRanking(Integer industryId, Integer fiscalYear, String reportPeriod,
                                   String indicatorCode, String order, Integer limit);

    /** 多条件交叉筛选 */
    ScreeningVO screening(ScreeningRequest req);

    /** 重算指标与行业对标(数据层 -> 计算层 -> 存储) */
    Map<String, Object> recalc(Integer industryId, Integer fiscalYear);
}

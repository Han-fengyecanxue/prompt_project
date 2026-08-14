package com.fycx.controller;

import com.fycx.controller.request.CompanyQueryRequest;
import com.fycx.controller.request.ScreeningRequest;
import com.fycx.controller.response.*;
import com.fycx.service.FinanceService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 财务数据接口: 公司查询 / 财务画像 / 指标趋势 / 行业对标 / 排名 / 交叉筛选 / 指标重算
 */
@RestController
@RequestMapping("/api/finance")
public class FinanceController {

    private final FinanceService financeService;

    public FinanceController(FinanceService financeService) {
        this.financeService = financeService;
    }

    /** 行业列表(含公司数量) */
    @GetMapping("/industries")
    public CommonResponse<List<IndustryVO>> industries() {
        return CommonResponse.success(financeService.listIndustries());
    }

    /** 公司分页查询(关键字/行业过滤) */
    @GetMapping("/companies")
    public CommonResponse<PageResult<CompanyVO>> companies(CompanyQueryRequest req) {
        return CommonResponse.success(financeService.pageCompanies(req));
    }

    /** 公司详情 */
    @GetMapping("/companies/{id}")
    public CommonResponse<CompanyVO> company(@PathVariable Integer id) {
        return CommonResponse.success(financeService.getCompany(id));
    }

    /** 财务画像(原始数据 + 指标 + 估值) */
    @GetMapping("/profile")
    public CommonResponse<ProfileVO> profile(@RequestParam Integer companyId,
                                             @RequestParam Integer fiscalYear,
                                             @RequestParam(defaultValue = "年报") String reportPeriod) {
        return CommonResponse.success(financeService.getProfile(companyId, fiscalYear, reportPeriod));
    }

    /** 多年度指标趋势(indicators 逗号分隔, 默认全部) */
    @GetMapping("/trend")
    public CommonResponse<List<TrendVO>> trend(@RequestParam Integer companyId,
                                               @RequestParam(required = false) List<String> indicators,
                                               @RequestParam(required = false) Integer startYear,
                                               @RequestParam(required = false) Integer endYear) {
        return CommonResponse.success(financeService.getTrend(companyId, indicators, startYear, endYear));
    }

    /** 行业对标(公司 vs 行业基准 + 百分位 + 排名) */
    @GetMapping("/benchmark")
    public CommonResponse<BenchmarkVO> benchmark(@RequestParam Integer companyId,
                                                 @RequestParam Integer fiscalYear,
                                                 @RequestParam(defaultValue = "年报") String reportPeriod) {
        return CommonResponse.success(financeService.getBenchmark(companyId, fiscalYear, reportPeriod));
    }

    /** 行业指标排名 */
    @GetMapping("/ranking")
    public CommonResponse<List<RankingItemVO>> ranking(@RequestParam Integer industryId,
                                                       @RequestParam Integer fiscalYear,
                                                       @RequestParam(defaultValue = "年报") String reportPeriod,
                                                       @RequestParam String indicatorCode,
                                                       @RequestParam(required = false) String order,
                                                       @RequestParam(required = false) Integer limit) {
        return CommonResponse.success(financeService.getRanking(industryId, fiscalYear, reportPeriod,
                indicatorCode, order, limit));
    }

    /** 多条件交叉筛选(AND) */
    @PostMapping("/screening")
    public CommonResponse<ScreeningVO> screening(@RequestBody ScreeningRequest req) {
        return CommonResponse.success(financeService.screening(req));
    }

    /** 重算财务指标与行业对标(可选 body: {"industryId":1,"fiscalYear":2025}, 不传则全量) */
    @PostMapping("/recalc")
    public CommonResponse<Map<String, Object>> recalc(@RequestBody(required = false) Map<String, Integer> body) {
        Integer industryId = body == null ? null : body.get("industryId");
        Integer fiscalYear = body == null ? null : body.get("fiscalYear");
        return CommonResponse.success(financeService.recalc(industryId, fiscalYear));
    }
}

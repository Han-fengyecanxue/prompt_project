package com.fycx.service.impl;

import com.fycx.common.ErrorCodeEnums;
import com.fycx.common.HandleException;
import com.fycx.common.IndicatorDef;
import com.fycx.controller.request.CompanyQueryRequest;
import com.fycx.controller.request.ScreeningCondition;
import com.fycx.controller.request.ScreeningRequest;
import com.fycx.controller.response.*;
import com.fycx.entity.*;
import com.fycx.mapper.*;
import com.fycx.service.FinanceService;
import com.fycx.service.calc.BenchmarkCalculator;
import com.fycx.service.calc.IndicatorCalcEngine;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 财务数据服务实现
 */
@Service
public class FinanceServiceImpl implements FinanceService {

    private static final Logger log = LoggerFactory.getLogger(FinanceServiceImpl.class);

    private final CompanyMapper companyMapper;
    private final FinancialDataMapper financialDataMapper;
    private final FinancialIndicatorMapper indicatorMapper;
    private final IndustryBenchmarkMapper benchmarkMapper;
    private final IndustryCategoryMapper industryMapper;
    private final ReportItemMapper reportItemMapper;
    private final ValuationSnapshotMapper valuationMapper;

    public FinanceServiceImpl(CompanyMapper companyMapper,
                              FinancialDataMapper financialDataMapper,
                              FinancialIndicatorMapper indicatorMapper,
                              IndustryBenchmarkMapper benchmarkMapper,
                              IndustryCategoryMapper industryMapper,
                              ReportItemMapper reportItemMapper,
                              ValuationSnapshotMapper valuationMapper) {
        this.companyMapper = companyMapper;
        this.financialDataMapper = financialDataMapper;
        this.indicatorMapper = indicatorMapper;
        this.benchmarkMapper = benchmarkMapper;
        this.industryMapper = industryMapper;
        this.reportItemMapper = reportItemMapper;
        this.valuationMapper = valuationMapper;
    }

    // ================== 基础查询 ==================

    @Override
    public List<IndustryVO> listIndustries() {
        return industryMapper.selectAllWithCount();
    }

    @Override
    public PageResult<CompanyVO> pageCompanies(CompanyQueryRequest req) {
        if (req == null) req = new CompanyQueryRequest();
        int page = req.getPage() == null || req.getPage() < 1 ? 1 : req.getPage();
        int size = req.getSize() == null || req.getSize() < 1 ? 10 : req.getSize();
        size = Math.min(size, 100);
        String keyword = StringUtils.hasText(req.getKeyword()) ? req.getKeyword().trim() : null;
        long total = companyMapper.countByCondition(keyword, req.getIndustryId(), req.getStatus());
        List<CompanyVO> list = companyMapper.selectByCondition(keyword, req.getIndustryId(), req.getStatus(),
                (page - 1) * size, size);
        return new PageResult<>(total, page, size, list);
    }

    @Override
    public CompanyVO getCompany(Integer companyId) {
        CompanyVO vo = companyMapper.selectVOByPrimaryKey(companyId);
        if (vo == null) {
            throw new HandleException(ErrorCodeEnums.COMPANY_NOT_EXIST);
        }
        return vo;
    }

    // ================== 财务画像 ==================

    @Override
    public ProfileVO getProfile(Integer companyId, Integer fiscalYear, String reportPeriod) {
        CompanyVO company = getCompany(companyId);
        reportPeriod = defaultPeriod(reportPeriod);
        ProfileVO vo = new ProfileVO();
        vo.setCompany(company);
        vo.setFiscalYear(fiscalYear);
        vo.setReportPeriod(reportPeriod);
        vo.setIndustryName(company.getIndustryName());

        List<RawItemVO> items = financialDataMapper.selectItemsByCompanyYear(companyId, fiscalYear, reportPeriod);
        List<FinancialIndicator> indicators = indicatorMapper.selectByCompanyYear(companyId, fiscalYear, reportPeriod);
        List<IndicatorVO> indicatorVOs = indicators.stream().map(this::toIndicatorVO).collect(Collectors.toList());
        ValuationSnapshot snapshot = valuationMapper.selectLatestByCompany(companyId);

        vo.setItems(items);
        vo.setIndicators(indicatorVOs);
        if (snapshot != null) {
            ValuationVO v = new ValuationVO();
            v.setSnapshotDate(snapshot.getSnapshotDate());
            v.setClosePrice(snapshot.getClosePrice());
            v.setMarketCap(snapshot.getMarketCap());
            vo.setValuation(v);
        }
        return vo;
    }

    // ================== 指标趋势 ==================

    @Override
    public List<TrendVO> getTrend(Integer companyId, List<String> indicators, Integer startYear, Integer endYear) {
        getCompany(companyId);
        int start = startYear == null ? 2021 : startYear;
        int end = endYear == null ? 2025 : endYear;
        if (start > end) throw new HandleException(ErrorCodeEnums.INVALID_PARAM.getCode(), "起始年份不能大于结束年份");

        List<String> codes = (indicators == null || indicators.isEmpty())
                ? IndicatorDef.allCodes() : indicators;
        // 去重并过滤未知编码
        List<IndicatorDef> defs = codes.stream()
                .map(IndicatorDef::fromCode)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());

        List<FinancialIndicator> all = indicatorMapper.selectByCompanyAllYears(companyId);
        Map<String, Map<Integer, BigDecimal>> byCode = new HashMap<>();
        for (FinancialIndicator ind : all) {
            byCode.computeIfAbsent(ind.getIndicatorCode(), k -> new HashMap<>())
                    .put(ind.getFiscalYear(), ind.getIndicatorValue());
        }

        List<TrendVO> result = new ArrayList<>();
        for (IndicatorDef def : defs) {
            Map<Integer, BigDecimal> yearMap = byCode.get(def.getCode());
            TrendVO trend = new TrendVO();
            trend.setIndicatorCode(def.getCode());
            trend.setIndicatorName(def.getName());
            trend.setUnit(def.getUnit());
            List<TrendPointVO> points = new ArrayList<>();
            if (yearMap != null) {
                for (int y = start; y <= end; y++) {
                    BigDecimal v = yearMap.get(y);
                    if (v == null) continue;
                    TrendPointVO p = new TrendPointVO();
                    p.setYear(y);
                    p.setValue(v);
                    points.add(p);
                }
            }
            trend.setPoints(points);
            result.add(trend);
        }
        return result;
    }

    // ================== 行业对标 ==================

    @Override
    public BenchmarkVO getBenchmark(Integer companyId, Integer fiscalYear, String reportPeriod) {
        CompanyVO company = getCompany(companyId);
        if (company.getIndustryId() == null) {
            throw new HandleException(ErrorCodeEnums.BENCHMARK_NOT_FOUND.getCode(), "该公司未归属行业, 无法对标");
        }
        reportPeriod = defaultPeriod(reportPeriod);

        // 公司该年度指标
        Map<String, FinancialIndicator> companyInds = indicatorMapper
                .selectByCompanyYear(companyId, fiscalYear, reportPeriod).stream()
                .collect(Collectors.toMap(FinancialIndicator::getIndicatorCode, i -> i, (a, b) -> a));

        // 行业该年度全部公司指标(联表)
        List<FinancialIndicator> industryInds = indicatorMapper
                .selectByIndustryYear(company.getIndustryId(), fiscalYear, reportPeriod);
        Map<String, List<BigDecimal>> industryValues = new HashMap<>();
        for (FinancialIndicator ind : industryInds) {
            industryValues.computeIfAbsent(ind.getIndicatorCode(), k -> new ArrayList<>())
                    .add(ind.getIndicatorValue());
        }

        BenchmarkVO vo = new BenchmarkVO();
        vo.setCompany(company);
        vo.setFiscalYear(fiscalYear);
        vo.setReportPeriod(reportPeriod);
        vo.setIndustryName(company.getIndustryName());

        List<BenchmarkItemVO> items = new ArrayList<>();
        for (IndicatorDef def : IndicatorDef.all()) {
            FinancialIndicator companyInd = companyInds.get(def.getCode());
            List<BigDecimal> values = industryValues.get(def.getCode());
            if (companyInd == null || values == null || values.isEmpty()) continue;

            BenchmarkItemVO item = new BenchmarkItemVO();
            item.setIndicatorCode(def.getCode());
            item.setIndicatorName(def.getName());
            item.setDimension(def.getDimension());
            item.setUnit(def.getUnit());
            item.setBetterDirection(def.getBetterDirection());
            item.setCompanyValue(companyInd.getIndicatorValue());

            BenchmarkCalculator.Stats stats = BenchmarkCalculator.stats(values);
            item.setAvgValue(stats.avg);
            item.setMedianValue(stats.median);
            item.setStdDev(stats.stdDev);
            item.setP25(stats.p25);
            item.setP75(stats.p75);
            item.setCompanyCount(stats.count);

            BigDecimal pct = BenchmarkCalculator.percentile(companyInd.getIndicatorValue(), values);
            item.setPercentile(pct);
            item.setScore(BenchmarkCalculator.score(pct, def.getBetterDirection()));
            item.setRank(BenchmarkCalculator.rank(companyInd.getIndicatorValue(), values, def.getBetterDirection()));
            item.setTotal(stats.count);
            items.add(item);
        }
        vo.setItems(items);
        return vo;
    }

    // ================== 行业排名 ==================

    @Override
    public List<RankingItemVO> getRanking(Integer industryId, Integer fiscalYear, String reportPeriod,
                                          String indicatorCode, String order, Integer limit) {
        IndicatorDef def = IndicatorDef.fromCode(indicatorCode);
        if (def == null) throw new HandleException(ErrorCodeEnums.INDICATOR_NOT_FOUND);
        if (industryId == null) throw new HandleException(ErrorCodeEnums.INVALID_PARAM.getCode(), "行业ID不能为空");
        reportPeriod = defaultPeriod(reportPeriod);

        List<FinancialIndicator> inds = indicatorMapper.selectByIndustryYear(industryId, fiscalYear, reportPeriod);
        Map<Integer, FinancialIndicator> byCompany = inds.stream()
                .filter(i -> indicatorCode.equals(i.getIndicatorCode()))
                .collect(Collectors.toMap(FinancialIndicator::getCompanyId, i -> i, (a, b) -> a));

        // 收集公司信息
        List<CompanyVO> companies = companyMapper.selectAllVO().stream()
                .filter(c -> industryId.equals(c.getIndustryId()))
                .collect(Collectors.toList());

        List<BigDecimal> values = byCompany.values().stream()
                .map(FinancialIndicator::getIndicatorValue)
                .collect(Collectors.toList());

        String direction = def.getBetterDirection();
        boolean asc = "asc".equalsIgnoreCase(order) || "lower_better".equals(direction) && !"desc".equalsIgnoreCase(order);

        List<RankingItemVO> result = new ArrayList<>();
        for (CompanyVO c : companies) {
            FinancialIndicator ind = byCompany.get(c.getCompanyId());
            if (ind == null) continue;
            RankingItemVO r = new RankingItemVO();
            r.setCompanyId(c.getCompanyId());
            r.setStockCode(c.getStockCode());
            r.setStockName(c.getStockName());
            r.setValue(ind.getIndicatorValue());
            r.setPercentile(BenchmarkCalculator.percentile(ind.getIndicatorValue(), values));
            r.setRank(BenchmarkCalculator.rank(ind.getIndicatorValue(), values, direction));
            result.add(r);
        }
        result.sort(Comparator.comparing(RankingItemVO::getRank));
        if (limit != null && limit > 0 && result.size() > limit) {
            result = result.subList(0, limit);
        }
        return result;
    }

    // ================== 多条件交叉筛选 ==================

    @Override
    public ScreeningVO screening(ScreeningRequest req) {
        if (req == null || req.getConditions() == null || req.getConditions().isEmpty()) {
            throw new HandleException(ErrorCodeEnums.SCREENING_NO_CONDITION);
        }
        Integer fiscalYear = req.getFiscalYear();
        if (fiscalYear == null) throw new HandleException(ErrorCodeEnums.INVALID_PARAM.getCode(), "财年不能为空");
        String reportPeriod = defaultPeriod(req.getReportPeriod());

        // 加载候选公司与指标
        List<FinancialIndicator> inds = req.getIndustryId() == null
                ? indicatorMapper.selectByYear(fiscalYear, reportPeriod)
                : indicatorMapper.selectByIndustryYear(req.getIndustryId(), fiscalYear, reportPeriod);
        if (inds.isEmpty()) {
            throw new HandleException(ErrorCodeEnums.NO_INDICATOR_DATA);
        }

        Map<Integer, Map<String, BigDecimal>> companyInds = new HashMap<>();
        Map<String, List<BigDecimal>> industryValues = new HashMap<>();
        for (FinancialIndicator ind : inds) {
            companyInds.computeIfAbsent(ind.getCompanyId(), k -> new HashMap<>())
                    .put(ind.getIndicatorCode(), ind.getIndicatorValue());
            industryValues.computeIfAbsent(ind.getIndicatorCode(), k -> new ArrayList<>())
                    .add(ind.getIndicatorValue());
        }

        // 公司信息映射
        Map<Integer, CompanyVO> companyMap = companyMapper.selectAllVO().stream()
                .filter(c -> companyInds.containsKey(c.getCompanyId()))
                .collect(Collectors.toMap(CompanyVO::getCompanyId, c -> c, (a, b) -> a));

        // 逐公司判定
        List<ScreeningItemVO> matched = new ArrayList<>();
        int conditionCount = req.getConditions().size();
        for (Map.Entry<Integer, Map<String, BigDecimal>> entry : companyInds.entrySet()) {
            Integer cid = entry.getKey();
            Map<String, BigDecimal> vals = entry.getValue();

            List<ScreeningDetailVO> details = new ArrayList<>();
            boolean allPass = true;
            for (ScreeningCondition cond : req.getConditions()) {
                ScreeningDetailVO detail = judge(cond, vals, industryValues);
                details.add(detail);
                if (!Boolean.TRUE.equals(detail.getPassed())) allPass = false;
            }
            if (allPass) {
                CompanyVO c = companyMap.get(cid);
                ScreeningItemVO item = new ScreeningItemVO();
                item.setCompanyId(cid);
                item.setStockCode(c == null ? null : c.getStockCode());
                item.setStockName(c == null ? null : c.getStockName());
                item.setIndustryName(c == null ? null : c.getIndustryName());
                item.setMatchedCount(conditionCount);
                item.setDetails(details);
                matched.add(item);
            }
        }

        // 分页
        int page = req.getPage() == null || req.getPage() < 1 ? 1 : req.getPage();
        int size = req.getSize() == null || req.getSize() < 1 ? 50 : req.getSize();
        int from = Math.min((page - 1) * size, matched.size());
        int to = Math.min(from + size, matched.size());

        ScreeningVO vo = new ScreeningVO();
        vo.setTotal(matched.size());
        vo.setConditionCount(conditionCount);
        vo.setCompanies(matched.subList(from, to));
        return vo;
    }

    /** 单条件判定 */
    private ScreeningDetailVO judge(ScreeningCondition cond, Map<String, BigDecimal> vals,
                                    Map<String, List<BigDecimal>> industryValues) {
        ScreeningDetailVO detail = new ScreeningDetailVO();
        detail.setIndicatorCode(cond.getIndicatorCode());
        IndicatorDef def = IndicatorDef.fromCode(cond.getIndicatorCode());
        detail.setIndicatorName(def == null ? cond.getIndicatorCode() : def.getName());
        detail.setOperator(cond.getOperator());
        detail.setValue(cond.getValue());
        detail.setValue2(cond.getValue2());

        BigDecimal actual = vals.get(cond.getIndicatorCode());
        detail.setActualValue(actual);
        if (actual == null) {
            detail.setPassed(false);
            return detail;
        }
        String op = cond.getOperator() == null ? "" : cond.getOperator();
        boolean pass;
        switch (op) {
            case "gt":
                pass = actual.compareTo(cond.getValue()) > 0;
                break;
            case "gte":
                pass = actual.compareTo(cond.getValue()) >= 0;
                break;
            case "lt":
                pass = actual.compareTo(cond.getValue()) < 0;
                break;
            case "lte":
                pass = actual.compareTo(cond.getValue()) <= 0;
                break;
            case "between":
                pass = actual.compareTo(cond.getValue()) >= 0
                        && actual.compareTo(cond.getValue2()) <= 0;
                break;
            case "pct_gt":
            case "pct_lt": {
                List<BigDecimal> values = industryValues.get(cond.getIndicatorCode());
                if (values == null || values.isEmpty()) {
                    pass = false;
                } else {
                    BigDecimal pct = BenchmarkCalculator.percentile(actual, values);
                    pass = "pct_gt".equals(op)
                            ? pct.compareTo(cond.getValue()) > 0
                            : pct.compareTo(cond.getValue()) < 0;
                }
                break;
            }
            default:
                throw new HandleException(ErrorCodeEnums.INVALID_PARAM.getCode(),
                        "不支持的筛选运算符: " + op);
        }
        detail.setPassed(pass);
        return detail;
    }

    // ================== 指标重算(数据层 -> 计算层 -> 存储) ==================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> recalc(Integer industryId, Integer fiscalYear) {
        List<CompanyVO> companies = companyMapper.selectAllVO();
        if (industryId != null) {
            companies = companies.stream()
                    .filter(c -> industryId.equals(c.getIndustryId()))
                    .collect(Collectors.toList());
        }
        if (companies.isEmpty()) {
            throw new HandleException(ErrorCodeEnums.COMPANY_NOT_EXIST.getCode(), "没有可重算的公司");
        }

        // 1. 按公司计算指标
        List<FinancialIndicator> allIndicators = new ArrayList<>();
        for (CompanyVO c : companies) {
            List<FinancialData> rawList = financialDataMapper.selectByCompanyAllYears(c.getCompanyId());
            // 按年度分组
            Map<Integer, Map<String, BigDecimal>> byYear = new TreeMap<>();
            for (FinancialData d : rawList) {
                String code = itemCodeOf(d.getItemId());
                if (code == null) continue;
                byYear.computeIfAbsent(d.getFiscalYear(), k -> new HashMap<>())
                        .put(code, d.getAmount());
            }
            List<Map.Entry<Integer, Map<String, BigDecimal>>> yearEntries = new ArrayList<>(byYear.entrySet());
            for (int i = 0; i < yearEntries.size(); i++) {
                Map.Entry<Integer, Map<String, BigDecimal>> e = yearEntries.get(i);
                Map<String, BigDecimal> prior = i == 0 ? null : yearEntries.get(i - 1).getValue();
                ValuationSnapshot valuation = snapshotForYear(c.getCompanyId(), e.getKey());
                if (fiscalYear != null && !fiscalYear.equals(e.getKey())) continue;
                allIndicators.addAll(IndicatorCalcEngine.calc(
                        c.getCompanyId(), e.getKey(), "年报", e.getValue(), prior, valuation));
            }
        }

        // 2. 全量覆盖写库
        indicatorMapper.deleteAll();
        if (!allIndicators.isEmpty()) {
            indicatorMapper.insertBatch(allIndicators);
        }

        // 3. 计算行业对标并写库
        benchmarkMapper.deleteAll();
        List<IndustryBenchmark> benchmarks = computeBenchmarks(companies, allIndicators);
        if (!benchmarks.isEmpty()) {
            benchmarkMapper.insertBatch(benchmarks);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("indicatorCount", allIndicators.size());
        result.put("benchmarkCount", benchmarks.size());
        result.put("message", "指标与行业对标重算完成");
        return result;
    }

    /** 从报表项目字典取编码(缓存) */
    private volatile Map<Integer, String> itemCodeCache;

    private String itemCodeOf(Integer itemId) {
        if (itemCodeCache == null) {
            synchronized (this) {
                if (itemCodeCache == null) {
                    Map<Integer, String> map = new HashMap<>();
                    for (ReportItem item : reportItemMapper.selectAll()) {
                        map.put(item.getItemId(), item.getItemCode());
                    }
                    itemCodeCache = map;
                }
            }
        }
        return itemCodeCache.get(itemId);
    }

    /** 取某年度对应的估值快照(仅同年快照, 保证 PE/PB 口径一致) */
    private ValuationSnapshot snapshotForYear(Integer companyId, Integer fiscalYear) {
        List<ValuationSnapshot> snapshots = valuationMapper.selectByCompany(companyId);
        if (snapshots.isEmpty()) return null;
        for (ValuationSnapshot s : snapshots) {
            Calendar cal = Calendar.getInstance();
            cal.setTime(s.getSnapshotDate());
            if (cal.get(Calendar.YEAR) == fiscalYear) return s;
        }
        return null;
    }

    /** 计算行业对标统计(按 行业x年度x指标) */
    private List<IndustryBenchmark> computeBenchmarks(List<CompanyVO> companies, List<FinancialIndicator> allIndicators) {
        // 公司 -> 行业 映射
        Map<Integer, Integer> companyIndustry = companies.stream()
                .collect(Collectors.toMap(CompanyVO::getCompanyId, CompanyVO::getIndustryId, (a, b) -> a));

        // 行业 -> 年度 -> 指标 -> 值列表
        Map<String, List<BigDecimal>> groups = new HashMap<>();
        for (FinancialIndicator ind : allIndicators) {
            Integer industryId = companyIndustry.get(ind.getCompanyId());
            if (industryId == null) continue;
            String key = industryId + "|" + ind.getFiscalYear() + "|" + ind.getReportPeriod() + "|" + ind.getIndicatorCode();
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(ind.getIndicatorValue());
        }

        List<IndustryBenchmark> result = new ArrayList<>();
        for (Map.Entry<String, List<BigDecimal>> entry : groups.entrySet()) {
            String[] parts = entry.getKey().split("\\|");
            IndustryBenchmark b = new IndustryBenchmark();
            b.setIndustryId(Integer.parseInt(parts[0]));
            b.setFiscalYear(Integer.parseInt(parts[1]));
            b.setReportPeriod(parts[2]);
            b.setIndicatorCode(parts[3]);

            BenchmarkCalculator.Stats stats = BenchmarkCalculator.stats(entry.getValue());
            b.setAvgValue(stats.avg);
            b.setMedianValue(stats.median);
            b.setStdDev(stats.stdDev);
            b.setP25(stats.p25);
            b.setP75(stats.p75);
            b.setCompanyCount(stats.count);
            result.add(b);
        }
        result.sort(Comparator.comparing(IndustryBenchmark::getIndustryId)
                .thenComparing(IndustryBenchmark::getFiscalYear)
                .thenComparing(IndustryBenchmark::getIndicatorCode));
        return result;
    }

    // ================== 工具 ==================

    private IndicatorVO toIndicatorVO(FinancialIndicator ind) {
        IndicatorVO vo = new IndicatorVO();
        IndicatorDef def = IndicatorDef.fromCode(ind.getIndicatorCode());
        vo.setIndicatorCode(ind.getIndicatorCode());
        vo.setIndicatorName(def == null ? ind.getIndicatorCode() : def.getName());
        vo.setDimension(def == null ? "其他" : def.getDimension());
        vo.setUnit(ind.getUnit());
        vo.setValue(ind.getIndicatorValue());
        vo.setBetterDirection(def == null ? "higher_better" : def.getBetterDirection());
        return vo;
    }

    private String defaultPeriod(String reportPeriod) {
        return StringUtils.hasText(reportPeriod) ? reportPeriod : "年报";
    }
}

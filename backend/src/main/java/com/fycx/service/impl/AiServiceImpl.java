package com.fycx.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fycx.common.ErrorCodeEnums;
import com.fycx.common.HandleException;
import com.fycx.common.IndicatorDef;
import com.fycx.controller.request.AiReportRequest;
import com.fycx.controller.request.ChatRequest;
import com.fycx.controller.request.ChatTurn;
import com.fycx.controller.response.BenchmarkItemVO;
import com.fycx.controller.response.BenchmarkVO;
import com.fycx.controller.response.CompanyVO;
import com.fycx.controller.response.PageResult;
import com.fycx.entity.AiReport;
import com.fycx.entity.PromptTemplate;
import com.fycx.mapper.AiReportMapper;
import com.fycx.mapper.PromptTemplateMapper;
import com.fycx.service.AiService;
import com.fycx.service.FinanceService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;

/**
 * AI 解读服务实现
 * 双层解耦: 底层数据由 FinanceService 精确计算 -> 组装"数据注入"层 -> 约束大模型基于数据生成报告
 * provider=mock 时无需 API Key, 由模板规则生成确定性报告(演示/离线可用)
 * provider=openai 时调用任意 OpenAI 兼容接口(DeepSeek/通义/智谱等)
 */
@Service
public class AiServiceImpl implements AiService {

    private static final Logger log = LoggerFactory.getLogger(AiServiceImpl.class);

    private final FinanceService financeService;
    private final PromptTemplateMapper promptTemplateMapper;
    private final AiReportMapper aiReportMapper;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final HttpClient httpClient;

    @Value("${ai.provider:mock}")
    private String provider;

    @Value("${ai.base-url:}")
    private String baseUrl;

    @Value("${ai.api-key:}")
    private String apiKey;

    @Value("${ai.model:deepseek-chat}")
    private String model;

    @Value("${ai.temperature:0.3}")
    private double temperature;

    @Value("${ai.timeout-seconds:60}")
    private int timeoutSeconds;

    public AiServiceImpl(FinanceService financeService,
                         PromptTemplateMapper promptTemplateMapper,
                         AiReportMapper aiReportMapper) {
        this.financeService = financeService;
        this.promptTemplateMapper = promptTemplateMapper;
        this.aiReportMapper = aiReportMapper;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    // ================== 模板 ==================

    @Override
    public List<PromptTemplate> listTemplates() {
        return promptTemplateMapper.selectEnabled();
    }

    // ================== 简报生成 ==================

    @Override
    public AiReport generateReport(AiReportRequest req) {
        if (req.getCompanyId() == null || req.getFiscalYear() == null) {
            throw new HandleException(ErrorCodeEnums.INVALID_PARAM.getCode(), "companyId 与 fiscalYear 不能为空");
        }
        String reportPeriod = StringUtils.hasText(req.getReportPeriod()) ? req.getReportPeriod() : "年报";

        BenchmarkVO benchmark = financeService.getBenchmark(req.getCompanyId(), req.getFiscalYear(), reportPeriod);
        if (benchmark.getItems().isEmpty()) {
            throw new HandleException(ErrorCodeEnums.NO_INDICATOR_DATA);
        }

        String dataJson = buildDataJson(benchmark);
        String systemPrompt = composeSystemPrompt(dataJson, req.getFiscalYear());
        String userPrompt = composeUserPrompt(benchmark, req.getFiscalYear(), req.getExtraInstruction());

        String answer = callLlm(systemPrompt, userPrompt, Collections.emptyList(), benchmark);

        return saveReport(benchmark.getCompany(), req.getFiscalYear(), reportPeriod, "brief",
                "生成" + req.getFiscalYear() + "年度财报解读简报", answer, dataJson);
    }

    // ================== 对话 ==================

    @Override
    public AiReport chat(ChatRequest req) {
        if (req.getCompanyId() == null || req.getFiscalYear() == null) {
            throw new HandleException(ErrorCodeEnums.INVALID_PARAM.getCode(), "companyId 与 fiscalYear 不能为空");
        }
        if (!StringUtils.hasText(req.getQuestion())) {
            throw new HandleException(ErrorCodeEnums.INVALID_PARAM.getCode(), "问题不能为空");
        }
        String reportPeriod = StringUtils.hasText(req.getReportPeriod()) ? req.getReportPeriod() : "年报";

        BenchmarkVO benchmark = financeService.getBenchmark(req.getCompanyId(), req.getFiscalYear(), reportPeriod);
        if (benchmark.getItems().isEmpty()) {
            throw new HandleException(ErrorCodeEnums.NO_INDICATOR_DATA);
        }

        String dataJson = buildDataJson(benchmark);
        String systemPrompt = composeSystemPrompt(dataJson, req.getFiscalYear());
        String userPrompt = "请基于注入的数据, 回答用户的追问问题。要求: 只使用注入数据中的数字, "
                + "不得编造; 若数据中不包含回答所需信息, 请明确说明。\n用户问题: " + req.getQuestion();

        List<ChatTurn> history = req.getHistory() == null ? Collections.emptyList() : req.getHistory();
        String answer = callLlm(systemPrompt, userPrompt, history, benchmark);

        return saveReport(benchmark.getCompany(), req.getFiscalYear(), reportPeriod, "chat",
                req.getQuestion(), answer, dataJson);
    }

    // ================== 报告记录 ==================

    @Override
    public PageResult<AiReport> listReports(Integer companyId, int page, int size) {
        if (page < 1) page = 1;
        if (size < 1) size = 10;
        size = Math.min(size, 100);
        long total = aiReportMapper.countByCompany(companyId);
        List<AiReport> list = aiReportMapper.selectByCompany(companyId, (page - 1) * size, size);
        return new PageResult<>(total, page, size, list);
    }

    @Override
    public AiReport getReport(Long reportId) {
        AiReport report = aiReportMapper.selectByPrimaryKey(reportId);
        if (report == null) {
            throw new HandleException(ErrorCodeEnums.DATA_NOT_FOUND.getCode(), "报告不存在");
        }
        return report;
    }

    // ================== 三层 Prompt 组装 ==================

    /** 数据注入层: 把精确计算结果序列化为 JSON */
    private String buildDataJson(BenchmarkVO benchmark) {
        try {
            Map<String, Object> root = new LinkedHashMap<>();
            CompanyVO c = benchmark.getCompany();
            Map<String, Object> company = new LinkedHashMap<>();
            company.put("公司ID", c.getCompanyId());
            company.put("股票代码", c.getStockCode());
            company.put("股票简称", c.getStockName());
            company.put("公司全称", c.getFullName());
            company.put("交易所", c.getExchange());
            company.put("所属行业", benchmark.getIndustryName());
            company.put("财年", benchmark.getFiscalYear());
            company.put("报告期", benchmark.getReportPeriod());
            root.put("company", company);

            List<Map<String, Object>> indicators = new ArrayList<>();
            for (BenchmarkItemVO item : benchmark.getItems()) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("指标编码", item.getIndicatorCode());
                m.put("指标名称", item.getIndicatorName());
                m.put("维度", item.getDimension());
                m.put("单位", item.getUnit());
                m.put("公司值", item.getCompanyValue());
                m.put("行业均值", item.getAvgValue());
                m.put("行业中位数", item.getMedianValue());
                m.put("P25", item.getP25());
                m.put("P75", item.getP75());
                m.put("行业样本数", item.getCompanyCount());
                m.put("行业百分位", item.getPercentile());
                m.put("行业评分(0-100越高越优)", item.getScore());
                m.put("行业排名", item.getRank() + "/" + item.getTotal());
                indicators.add(m);
            }
            root.put("indicators", indicators);
            return objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(root);
        } catch (Exception e) {
            log.error("构建数据JSON失败", e);
            throw new HandleException(ErrorCodeEnums.AI_SERVICE_ERROR);
        }
    }

    /** 组装 system prompt: 角色设定 + 数据注入 */
    private String composeSystemPrompt(String dataJson, Integer fiscalYear) {
        String role = getTemplate("角色设定");
        String dataInject = getTemplate("数据注入");
        dataInject = dataInject.replace("{fiscalYear}", String.valueOf(fiscalYear))
                .replace("{data_json}", dataJson);
        return role + "\n\n" + dataInject;
    }

    /** 组装 user prompt: 输出约束 + 用户要求 */
    private String composeUserPrompt(BenchmarkVO benchmark, Integer fiscalYear, String extraInstruction) {
        String outputConstraint = getTemplate("输出约束");
        String instruction = StringUtils.hasText(extraInstruction) ? extraInstruction
                : "请基于注入的数据, 生成" + benchmark.getCompany().getStockName()
                + "(" + benchmark.getCompany().getStockCode() + ")" + fiscalYear + "年度财报解读简报。";
        return outputConstraint + "\n\n" + instruction;
    }

    /** 读取模板(DB优先, 内置默认兜底) */
    private String getTemplate(String type) {
        List<PromptTemplate> templates = promptTemplateMapper.selectEnabled();
        for (PromptTemplate t : templates) {
            if (type.equals(t.getTemplateType())) {
                return t.getTemplateContent();
            }
        }
        return defaultTemplate(type);
    }

    private String defaultTemplate(String type) {
        switch (type) {
            case "角色设定":
                return "你是一位资深的上司公司财务分析师, 拥有 CFA 资质与 10 年以上 A 股财报分析经验, "
                        + "擅长通过财务指标对上市公司进行客观诊断, 并以通俗易懂的语言向普通投资者解释专业结论。"
                        + "你的分析风格: 客观、严谨、克制, 不夸大、不唱多、不唱空, 结论必须有数据支撑。";
            case "数据注入":
                return "以下是由系统精确计算出的【该公司】{fiscalYear}年财务指标与行业对标数据(JSON 格式), "
                        + "这是本次分析唯一可信的数据来源:\n{data_json}\n"
                        + "行业对标口径: 行业均值/中位数/P25/P75 基于同行业上市公司同一年度数据计算; "
                        + "百分位排名表示该公司指标值在行业内所处位置(0-100, 越高表示相对越优)。";
            case "输出约束":
                return "请严格按照以下要求输出解读报告:\n"
                        + "1. 只能使用【数据注入】中提供的数据, 严禁编造、推断或补充任何数据注入中不存在的数字;\n"
                        + "2. 报告结构固定为: 一、公司概览; 二、盈利能力分析; 三、成长性分析; 四、财务风险分析; "
                        + "五、估值水平分析; 六、综合结论与风险提示;\n"
                        + "3. 每个章节必须引用具体指标数值与行业对标结果(如: ROE 为 25.3%, 高于行业中位数 18.2%);\n"
                        + "4. 结论部分给出综合评级(优秀/良好/一般/偏弱)与理由;\n"
                        + "5. 使用中文、Markdown 格式, 控制在 800 字以内;\n"
                        + "6. 如果某维度数据缺失, 明确说明\"该维度数据不足, 无法分析\", 不得猜测。";
            default:
                return "";
        }
    }

    // ================== LLM 调用 ==================

    private String callLlm(String systemPrompt, String userPrompt, List<ChatTurn> history, BenchmarkVO benchmark) {
        if ("openai".equalsIgnoreCase(provider) && StringUtils.hasText(apiKey)) {
            try {
                return callOpenAICompatible(systemPrompt, userPrompt, history);
            } catch (Exception e) {
                log.error("大模型调用失败, 降级为Mock: {}", e.getMessage());
                return mockGenerate(benchmark, userPrompt, false);
            }
        }
        return mockGenerate(benchmark, userPrompt, history != null && !history.isEmpty());
    }

    /** OpenAI 兼容接口调用 */
    private String callOpenAICompatible(String systemPrompt, String userPrompt, List<ChatTurn> history) throws Exception {
        String url = baseUrl.endsWith("/") ? baseUrl + "chat/completions" : baseUrl + "/chat/completions";

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", model);
        body.put("temperature", temperature);
        body.put("stream", false);
        List<Map<String, String>> messages = new ArrayList<>();
        messages.add(msg("system", systemPrompt));
        for (ChatTurn turn : history) {
            messages.add(msg(turn.getRole(), turn.getContent()));
        }
        messages.add(msg("user", userPrompt));
        body.put("messages", messages);

        String json = objectMapper.writeValueAsString(body);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(json, java.nio.charset.StandardCharsets.UTF_8))
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new RuntimeException("LLM HTTP " + response.statusCode() + ": " + response.body());
        }
        JsonNode root = objectMapper.readTree(response.body());
        JsonNode content = root.path("choices").path(0).path("message").path("content");
        if (content.isMissingNode()) {
            throw new RuntimeException("LLM 响应缺少 content: " + response.body());
        }
        return content.asText();
    }

    private Map<String, String> msg(String role, String content) {
        Map<String, String> m = new LinkedHashMap<>();
        m.put("role", role);
        m.put("content", content);
        return m;
    }

    // ================== Mock 生成器(确定性, 防幻觉演示) ==================

    /**
     * 基于注入数据生成结构化报告/回答, 所有数字均取自数据上下文, 不编造
     */
    private String mockGenerate(BenchmarkVO benchmark, String userPrompt, boolean isChat) {
        CompanyVO c = benchmark.getCompany();
        List<BenchmarkItemVO> items = benchmark.getItems();
        Map<String, BenchmarkItemVO> byCode = items.stream()
                .collect(Collectors.toMap(BenchmarkItemVO::getIndicatorCode, i -> i, (a, b) -> a));

        if (isChat || userPrompt.contains("追问") || userPrompt.contains("问题")) {
            return mockChatAnswer(c, byCode, userPrompt);
        }
        return mockBrief(c, benchmark.getFiscalYear(), byCode);
    }

    private String mockBrief(CompanyVO c, Integer fiscalYear, Map<String, BenchmarkItemVO> byCode) {
        StringBuilder sb = new StringBuilder();
        sb.append("# ").append(c.getStockName()).append("(").append(c.getStockCode())
                .append(") ").append(fiscalYear).append("年度财报解读简报\n\n");

        // 一、公司概览
        sb.append("## 一、公司概览\n");
        sb.append("- 所属行业: ").append(industryName(c)).append("\n");
        BenchmarkItemVO eps = byCode.get("eps");
        if (eps != null) {
            sb.append("- 基本每股收益: ").append(fmt(eps.getCompanyValue())).append(" 元/股\n");
        }
        sb.append("\n");

        // 二、盈利能力
        sb.append("## 二、盈利能力分析\n");
        appendDim(sb, byCode, "roe", "ROE(净资产收益率)");
        appendDim(sb, byCode, "gross_margin", "毛利率");
        appendDim(sb, byCode, "net_margin_parent", "归母净利率");
        sb.append("\n");

        // 三、成长性
        sb.append("## 三、成长性分析\n");
        appendDim(sb, byCode, "revenue_growth", "营业收入增长率");
        appendDim(sb, byCode, "profit_growth", "归母净利润增长率");
        sb.append("\n");

        // 四、财务风险
        sb.append("## 四、财务风险分析\n");
        appendDim(sb, byCode, "asset_liability_ratio", "资产负债率");
        appendDim(sb, byCode, "current_ratio", "流动比率");
        appendDim(sb, byCode, "quick_ratio", "速动比率");
        sb.append("\n");

        // 五、估值
        sb.append("## 五、估值水平分析\n");
        appendDim(sb, byCode, "pe", "市盈率PE");
        appendDim(sb, byCode, "pb", "市净率PB");
        sb.append("\n");

        // 六、综合结论
        sb.append("## 六、综合结论与风险提示\n");
        sb.append("综合评级: ").append(overallRating(byCode)).append("\n\n");
        sb.append("- 以上所有数据均由系统精确计算并注入, 未作任何推测或编造。\n");
        sb.append("- 风险提示: 本报告基于历史财务数据, 不构成投资建议; 行业对标样本为同行业上市公司, 样本量有限。\n");
        return sb.toString();
    }

    private void appendDim(StringBuilder sb, Map<String, BenchmarkItemVO> byCode, String code, String label) {
        BenchmarkItemVO item = byCode.get(code);
        if (item == null || item.getCompanyValue() == null) {
            sb.append("- ").append(label).append(": 该维度数据不足, 无法分析\n");
            return;
        }
        sb.append("- ").append(label).append(": ").append(fmt(item.getCompanyValue()))
                .append(" ").append(item.getUnit() == null ? "" : item.getUnit())
                .append(" | 行业中位数: ").append(fmt(item.getMedianValue()))
                .append(" | 行业评分: ").append(fmt(item.getScore()))
                .append(" (排名 ").append(item.getRank()).append("/").append(item.getTotal()).append(")\n");
    }

    private String overallRating(Map<String, BenchmarkItemVO> byCode) {
        List<String> dims = Arrays.asList("roe", "gross_margin", "net_margin_parent",
                "revenue_growth", "profit_growth", "current_ratio", "quick_ratio");
        List<BigDecimal> scores = new ArrayList<>();
        for (String code : dims) {
            BenchmarkItemVO item = byCode.get(code);
            if (item != null && item.getScore() != null) scores.add(item.getScore());
        }
        if (scores.isEmpty()) return "一般(数据不足)";
        BigDecimal avg = scores.stream().reduce(BigDecimal.ZERO, BigDecimal::add)
                .divide(BigDecimal.valueOf(scores.size()), 1, java.math.RoundingMode.HALF_UP);
        if (avg.compareTo(new BigDecimal("75")) >= 0) return "优秀";
        if (avg.compareTo(new BigDecimal("55")) >= 0) return "良好";
        if (avg.compareTo(new BigDecimal("35")) >= 0) return "一般";
        return "偏弱";
    }

    /** Mock 对话: 基于关键词返回数据锚定的回答 */
    private String mockChatAnswer(CompanyVO c, Map<String, BenchmarkItemVO> byCode, String question) {
        String q = question == null ? "" : question;
        String ql = q.toLowerCase();
        List<BenchmarkItemVO> candidates = new ArrayList<>();
        for (BenchmarkItemVO item : byCode.values()) {
            if (item.getCompanyValue() == null) continue;
            IndicatorDef def = IndicatorDef.fromCode(item.getIndicatorCode());
            boolean hit = false;
            if (def != null) {
                for (String alias : def.getAliases()) {
                    if (alias.equals(alias.toLowerCase()) ? ql.contains(alias) : q.contains(alias)) {
                        hit = true;
                        break;
                    }
                }
            }
            if (hit) candidates.add(item);
        }
        // 关键词维度匹配
        if (candidates.isEmpty()) {
            if (q.contains("盈利")) {
                addByCode(candidates, byCode, "roe", "gross_margin", "net_margin_parent");
            } else if (q.contains("成长") || q.contains("增长")) {
                addByCode(candidates, byCode, "revenue_growth", "profit_growth");
            } else if (q.contains("风险") || q.contains("负债") || q.contains("偿债")) {
                addByCode(candidates, byCode, "asset_liability_ratio", "current_ratio", "quick_ratio");
            } else if (q.contains("估值") || q.contains("市盈") || q.contains("市净")) {
                addByCode(candidates, byCode, "pe", "pb");
            } else if (q.contains("现金流")) {
                addByCode(candidates, byCode, "cashflow_quality");
            }
        }
        if (candidates.isEmpty()) {
            return "根据注入的数据, 我可以回答关于" + c.getStockName()
                    + "的盈利能力(ROE/毛利率/净利率)、成长性(营收/利润增长率)、财务风险(资产负债率/流动比率/速动比率)、"
                    + "估值(PE/PB)、盈利质量(经营现金流/净利润)等问题。请尝试提问这些方面的具体问题。"
                    + "注意: 我只能使用系统注入的数据回答, 超出数据范围的问题无法回答。";
        }
        StringBuilder sb = new StringBuilder();
        sb.append("根据系统注入的").append(c.getStockName()).append("数据, 回答如下:\n");
        for (BenchmarkItemVO item : candidates) {
            sb.append("- ").append(item.getIndicatorName()).append(": ").append(fmt(item.getCompanyValue()))
                    .append(" ").append(item.getUnit() == null ? "" : item.getUnit())
                    .append("; 行业中位数 ").append(fmt(item.getMedianValue()))
                    .append(", 行业评分 ").append(fmt(item.getScore()))
                    .append(", 排名 ").append(item.getRank()).append("/").append(item.getTotal()).append("\n");
        }
        sb.append("以上数据均来自系统精确计算并注入, 未作推测。");
        return sb.toString();
    }

    private void addByCode(List<BenchmarkItemVO> list, Map<String, BenchmarkItemVO> byCode, String... codes) {
        for (String code : codes) {
            BenchmarkItemVO item = byCode.get(code);
            if (item != null && item.getCompanyValue() != null) list.add(item);
        }
    }

    private String industryName(CompanyVO c) {
        return c.getIndustryName() == null ? "未知" : c.getIndustryName();
    }

    private String fmt(BigDecimal v) {
        return v == null ? "—" : v.stripTrailingZeros().toPlainString();
    }

    // ================== 保存 ==================

    private AiReport saveReport(CompanyVO company, Integer fiscalYear, String reportPeriod,
                                String reportType, String question, String answer, String context) {
        AiReport report = new AiReport();
        report.setCompanyId(company.getCompanyId());
        report.setFiscalYear(fiscalYear);
        report.setReportPeriod(reportPeriod);
        report.setReportType(reportType);
        report.setUserQuestion(question);
        report.setAiAnswer(answer);
        report.setContext(context);
        report.setCreateTime(new Date());
        aiReportMapper.insert(report);
        return report;
    }
}

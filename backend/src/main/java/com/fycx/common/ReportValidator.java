package com.fycx.common;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 数值幻觉校验器 (移植自 docs/report_validator.py)
 * 原理: 报告中的每个数字都应能在"注入上下文(计算层JSON)"中找到锚点来源。
 *   可溯源: 报告数字 四舍五入到3位 后能在注入JSON锚点集合中命中(等价 abs<=0.0005)。
 *   可疑(疑似幻觉): 未能命中锚点的数字。
 */
public final class ReportValidator {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    /** 日期序列(如 2023-12-31)不参与比对 */
    private static final Pattern DATE_RE = Pattern.compile("\\d{4}-\\d{2}-\\d{2}");
    /** 通用数字(整数/小数) */
    private static final Pattern NUM_RE = Pattern.compile("\\d+(?:\\.\\d+)?");
    /** 排名串: 3/8 */
    private static final Pattern RANK_RE = Pattern.compile("\\d+/\\d+");
    /** 纯数字字符串(股票代码等 4~6 位) */
    private static final Pattern DIGITS_RE = Pattern.compile("\\d{4,6}");

    private ReportValidator() {
    }

    /** 从注入上下文 JSON 提取全部锚点数值(3位舍入) */
    public static Set<BigDecimal> extractAnchors(String contextJson) {
        Set<BigDecimal> anchors = new HashSet<>();
        if (contextJson == null || contextJson.isBlank()) {
            return anchors;
        }
        try {
            walk(MAPPER.readTree(contextJson), anchors);
        } catch (Exception ignored) {
            // 无法解析则无锚点, 视全部数字为可疑
        }
        return anchors;
    }

    private static void walk(JsonNode node, Set<BigDecimal> anchors) {
        if (node == null) {
            return;
        }
        if (node.isObject()) {
            node.fields().forEachRemaining(e -> walk(e.getValue(), anchors));
        } else if (node.isArray()) {
            node.forEach(n -> walk(n, anchors));
        } else if (node.isNumber()) {
            anchors.add(r3(node.decimalValue()));
        } else if (node.isTextual()) {
            String s = node.asText().trim();
            if (RANK_RE.matcher(s).matches()) {
                String[] p = s.split("/");
                anchors.add(r3(new BigDecimal(p[0])));
                anchors.add(r3(new BigDecimal(p[1])));
            } else if (DIGITS_RE.matcher(s).matches()) {
                anchors.add(r3(new BigDecimal(s)));
            }
        }
    }

    private static BigDecimal r3(BigDecimal v) {
        return v.setScale(3, RoundingMode.HALF_UP);
    }

    /** 从文本提取数字(剔除日期序列) */
    public static List<BigDecimal> extractNumbers(String text) {
        if (text == null) {
            return Collections.emptyList();
        }
        String noDate = DATE_RE.matcher(text).replaceAll(" ");
        List<BigDecimal> out = new ArrayList<>();
        Matcher m = NUM_RE.matcher(noDate);
        while (m.find()) {
            out.add(new BigDecimal(m.group()));
        }
        return out;
    }

    /** 校验: 计算可溯源数/可疑数/引用准确率 */
    public static Result validate(String answer, String contextJson) {
        Set<BigDecimal> anchors = extractAnchors(contextJson);
        List<BigDecimal> nums = extractNumbers(answer);
        List<BigDecimal> suspicious = new ArrayList<>();
        int matched = 0;
        for (BigDecimal n : nums) {
            if (anchors.contains(r3(n))) {
                matched++;
            } else {
                suspicious.add(r3(n));
            }
        }
        double acc = nums.isEmpty() ? 100.0 : (double) matched / nums.size() * 100.0;
        return new Result(nums.size(), matched,
                BigDecimal.valueOf(acc).setScale(1, RoundingMode.HALF_UP).doubleValue(),
                suspicious);
    }

    /** 校验结果 */
    public static final class Result {
        private final int nums;
        private final int matched;
        private final double accuracy;
        private final List<BigDecimal> suspicious;

        Result(int nums, int matched, double accuracy, List<BigDecimal> suspicious) {
            this.nums = nums;
            this.matched = matched;
            this.accuracy = accuracy;
            this.suspicious = suspicious;
        }

        public int getNums() {
            return nums;
        }

        public int getMatched() {
            return matched;
        }

        public double getAccuracy() {
            return accuracy;
        }

        public int getSuspiciousCount() {
            return suspicious.size();
        }

        public List<BigDecimal> getSuspicious() {
            return suspicious;
        }
    }
}
package com.fycx.service.calc;

import com.fycx.common.IndicatorDef;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 * 行业对标统计引擎
 * 计算: 均值/中位数/标准差/P25/P75/公司数量 + 百分位排名 + 名次
 * 排名方向: higher_better 指标值越大排名越靠前; lower_better 指标值越小排名越靠前
 */
public class BenchmarkCalculator {

    private BenchmarkCalculator() {
    }

    /** 行业统计结果 */
    public static class Stats {
        public BigDecimal avg;
        public BigDecimal median;
        public BigDecimal stdDev;
        public BigDecimal p25;
        public BigDecimal p75;
        public int count;
    }

    /** 计算一组值的统计量(忽略 null) */
    public static Stats stats(List<BigDecimal> rawValues) {
        Stats s = new Stats();
        List<BigDecimal> values = new ArrayList<>();
        for (BigDecimal v : rawValues) {
            if (v != null) values.add(v);
        }
        s.count = values.size();
        if (values.isEmpty()) return s;

        values.sort(Comparator.naturalOrder());

        // 均值
        BigDecimal sum = BigDecimal.ZERO;
        for (BigDecimal v : values) sum = sum.add(v);
        s.avg = sum.divide(BigDecimal.valueOf(values.size()), 4, RoundingMode.HALF_UP);

        // 中位数
        s.median = quantile(values, 0.5);
        s.p25 = quantile(values, 0.25);
        s.p75 = quantile(values, 0.75);

        // 标准差(总体标准差)
        BigDecimal variance = BigDecimal.ZERO;
        for (BigDecimal v : values) {
            BigDecimal diff = v.subtract(s.avg);
            variance = variance.add(diff.multiply(diff));
        }
        variance = variance.divide(BigDecimal.valueOf(values.size()), 8, RoundingMode.HALF_UP);
        s.stdDev = BigDecimal.valueOf(Math.sqrt(variance.doubleValue())).setScale(4, RoundingMode.HALF_UP);
        return s;
    }

    /** 线性插值分位数 */
    private static BigDecimal quantile(List<BigDecimal> sorted, double q) {
        int n = sorted.size();
        if (n == 1) return sorted.get(0);
        double pos = q * (n - 1);
        int lo = (int) Math.floor(pos);
        int hi = (int) Math.ceil(pos);
        if (lo == hi) return sorted.get(lo);
        BigDecimal vLo = sorted.get(lo);
        BigDecimal vHi = sorted.get(hi);
        double frac = pos - lo;
        return vLo.add(vHi.subtract(vLo).multiply(BigDecimal.valueOf(frac))).setScale(4, RoundingMode.HALF_UP);
    }

    /**
     * 原始百分位(0-100): 值越大, 数值在行业中的位置越高
     * 定义: (严格小于该值的样本数) / (样本数-1) * 100; 样本数=1 或全部相等时取 50
     */
    public static BigDecimal percentile(BigDecimal v, List<BigDecimal> rawValues) {
        if (v == null) return null;
        List<BigDecimal> values = new ArrayList<>();
        for (BigDecimal x : rawValues) {
            if (x != null) values.add(x);
        }
        if (values.isEmpty()) return null;
        if (values.size() == 1) return new BigDecimal("50");

        int below = 0;
        boolean allEqual = true;
        BigDecimal first = values.get(0);
        for (BigDecimal x : values) {
            if (x.compareTo(v) < 0) below++;
            if (x.compareTo(first) != 0) allEqual = false;
        }
        if (allEqual) return new BigDecimal("50");
        return BigDecimal.valueOf(below * 100.0 / (values.size() - 1)).setScale(1, RoundingMode.HALF_UP);
    }

    /**
     * 方向调整后的评分(0-100, 越高越优):
     * higher_better -> score = 原始百分位
     * lower_better  -> score = 100 - 原始百分位
     */
    public static BigDecimal score(BigDecimal percentile, String betterDirection) {
        if (percentile == null) return null;
        if ("lower_better".equals(betterDirection)) {
            return BigDecimal.valueOf(100).subtract(percentile);
        }
        return percentile;
    }

    /**
     * 名次(1 = 最优)
     */
    public static int rank(BigDecimal v, List<BigDecimal> rawValues, String betterDirection) {
        if (v == null) return 0;
        List<BigDecimal> values = new ArrayList<>();
        for (BigDecimal x : rawValues) {
            if (x != null) values.add(x);
        }
        if (values.isEmpty()) return 0;
        boolean higherBetter = !"lower_better".equals(betterDirection);
        // 升序排序后, 找到 v 的插入位置
        values.sort(Comparator.naturalOrder());
        int pos = 0;
        for (int i = 0; i < values.size(); i++) {
            if (values.get(i).compareTo(v) >= 0) {
                pos = i;
                break;
            }
            pos = i + 1;
        }
        // pos 是升序名次(1为最小); 反转得到 1为最优
        if (higherBetter) {
            return values.size() - pos;
        }
        return pos + 1;
    }

    /** 按指标方向排序比较器 */
    public static Comparator<BigDecimal> valueComparator(String betterDirection) {
        if ("lower_better".equals(betterDirection)) {
            return Comparator.naturalOrder();
        }
        return Comparator.reverseOrder();
    }

    /** 排名用: 排序后的完整列表(含公司ID映射由调用方处理) */
    public static List<BigDecimal> sortedValues(List<BigDecimal> rawValues, String betterDirection) {
        List<BigDecimal> values = new ArrayList<>();
        for (BigDecimal v : rawValues) {
            if (v != null) values.add(v);
        }
        values.sort(valueComparator(betterDirection));
        return values;
    }

    /** 兼容: 供需要 IndicatorDef 的调用 */
    public static String directionOf(String indicatorCode) {
        IndicatorDef def = IndicatorDef.fromCode(indicatorCode);
        return def == null ? "higher_better" : def.getBetterDirection();
    }
}

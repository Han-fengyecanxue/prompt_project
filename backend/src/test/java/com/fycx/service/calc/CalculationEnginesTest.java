package com.fycx.service.calc;

import com.fycx.entity.FinancialIndicator;
import com.fycx.entity.ValuationSnapshot;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

class CalculationEnginesTest {

    @Test
    void calculatesFinancialRatiosAndYearOverYearGrowth() {
        // total_equity(所有者权益合计) 与 total_equity_parent(归母权益) 故意取不同值:
        // ROE 必须用后者, 否则本用例会算出 40% 而不是 50%。
        Map<String, BigDecimal> current = values(
                "operating_revenue", "200",
                "operating_cost", "100",
                "net_profit", "40",
                "net_profit_parent", "40",
                "total_equity", "100",
                "total_equity_parent", "80",
                "total_assets", "200",
                "total_liabilities", "100",
                "current_assets_total", "60",
                "current_liabilities_total", "30",
                "inventory", "15",
                "operating_cashflow", "32",
                "eps_basic", "2.5");
        Map<String, BigDecimal> prior = values(
                "operating_revenue", "100",
                "net_profit_parent", "20",
                "total_equity", "100",
                "total_equity_parent", "80");

        Map<String, BigDecimal> actual = IndicatorCalcEngine.calc(1, 2024, "年报", current, prior, null)
                .stream().collect(Collectors.toMap(FinancialIndicator::getIndicatorCode,
                        FinancialIndicator::getIndicatorValue));

        assertEquals(new BigDecimal("50.0000"), actual.get("roe"));
        assertEquals(new BigDecimal("50.0000"), actual.get("gross_margin"));
        assertEquals(new BigDecimal("100.0000"), actual.get("revenue_growth"));
        assertEquals(new BigDecimal("100.0000"), actual.get("profit_growth"));
        assertEquals(new BigDecimal("2.0000"), actual.get("current_ratio"));
        assertEquals(new BigDecimal("1.5000"), actual.get("quick_ratio"));
        assertEquals(new BigDecimal("0.8000"), actual.get("cashflow_quality"));
    }

    /**
     * 回归用例: ROE/PB 的分母必须是"归属于母公司股东的权益", 不是"所有者权益合计"。
     * 两者取不同值时, 若实现误用合计权益, ROE 会变成 15%、PB 会变成 4。
     */
    @Test
    void roeAndPbUseParentEquityInsteadOfTotalEquity() {
        Map<String, BigDecimal> current = values(
                "net_profit_parent", "30",
                "total_equity", "200",
                "total_equity_parent", "100");
        Map<String, BigDecimal> prior = values(
                "net_profit_parent", "10",
                "total_equity", "200",
                "total_equity_parent", "100");
        ValuationSnapshot valuation = new ValuationSnapshot();
        valuation.setMarketCap(new BigDecimal("800"));

        Map<String, BigDecimal> actual = IndicatorCalcEngine.calc(1, 2024, "年报", current, prior, valuation)
                .stream().collect(Collectors.toMap(FinancialIndicator::getIndicatorCode,
                        FinancialIndicator::getIndicatorValue));

        // ROE = 30 / ((100+100)/2) = 30%   (误用合计权益则为 30/((200+200)/2) = 15%)
        assertEquals(new BigDecimal("30.0000"), actual.get("roe"));
        // PB = 800 / 100 = 8            (误用合计权益则为 800/200 = 4)
        assertEquals(new BigDecimal("8.0000"), actual.get("pb"));
        // PE 用归母净利润, 不受本次口径修正影响: 800 / 30
        assertEquals(new BigDecimal("26.6667"), actual.get("pe"));
    }

    @Test
    void omitsIndicatorsWithMissingInputsOrZeroDenominators() {
        Map<String, BigDecimal> current = values(
                "operating_revenue", "0",
                "operating_cost", "10",
                "net_profit", "5",
                "net_profit_parent", "5",
                "total_equity", "0",
                "total_equity_parent", "0",
                "total_assets", "0",
                "total_liabilities", "1",
                "current_assets_total", "10",
                "current_liabilities_total", "0",
                "inventory", "2");

        List<FinancialIndicator> result = IndicatorCalcEngine.calc(1, 2024, "年报", current, null, null);
        Map<String, BigDecimal> actual = result.stream().collect(Collectors.toMap(
                FinancialIndicator::getIndicatorCode, FinancialIndicator::getIndicatorValue));

        assertFalse(actual.containsKey("roe"));
        assertFalse(actual.containsKey("gross_margin"));
        assertFalse(actual.containsKey("net_margin_parent"));
        assertFalse(actual.containsKey("revenue_growth"));
        assertFalse(actual.containsKey("current_ratio"));
        assertFalse(actual.containsKey("quick_ratio"));
        assertFalse(actual.containsKey("eps"));
    }

    @Test
    void calculatesIndustryStatisticsPercentilesAndDirectionAwareRanks() {
        List<BigDecimal> sample = Arrays.asList(decimal("1"), decimal("2"), decimal("3"), decimal("4"));
        BenchmarkCalculator.Stats stats = BenchmarkCalculator.stats(sample);

        assertEquals(decimal("2.5000"), stats.avg);
        assertEquals(decimal("2.5000"), stats.median);
        assertEquals(decimal("1.7500"), stats.p25);
        assertEquals(decimal("3.2500"), stats.p75);
        assertEquals(decimal("1.1180"), stats.stdDev);
        assertEquals(decimal("66.7"), BenchmarkCalculator.percentile(decimal("3"), sample));
        assertEquals(1, BenchmarkCalculator.rank(decimal("4"), sample, "higher_better"));
        assertEquals(1, BenchmarkCalculator.rank(decimal("1"), sample, "lower_better"));
    }

    private static Map<String, BigDecimal> values(String... pairs) {
        Map<String, BigDecimal> values = new HashMap<>();
        for (int i = 0; i < pairs.length; i += 2) {
            values.put(pairs[i], decimal(pairs[i + 1]));
        }
        return values;
    }

    private static BigDecimal decimal(String value) {
        return new BigDecimal(value);
    }
}
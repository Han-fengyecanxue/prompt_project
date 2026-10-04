package com.fycx.service.calc;

import com.fycx.entity.FinancialIndicator;
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
        Map<String, BigDecimal> current = values(
                "operating_revenue", "200",
                "operating_cost", "100",
                "net_profit", "40",
                "net_profit_parent", "40",
                "total_equity", "100",
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
                "total_equity", "100");

        Map<String, BigDecimal> actual = IndicatorCalcEngine.calc(1, 2024, "年报", current, prior, null)
                .stream().collect(Collectors.toMap(FinancialIndicator::getIndicatorCode,
                        FinancialIndicator::getIndicatorValue));

        assertEquals(new BigDecimal("40.0000"), actual.get("roe"));
        assertEquals(new BigDecimal("50.0000"), actual.get("gross_margin"));
        assertEquals(new BigDecimal("100.0000"), actual.get("revenue_growth"));
        assertEquals(new BigDecimal("100.0000"), actual.get("profit_growth"));
        assertEquals(new BigDecimal("2.0000"), actual.get("current_ratio"));
        assertEquals(new BigDecimal("1.5000"), actual.get("quick_ratio"));
        assertEquals(new BigDecimal("0.8000"), actual.get("cashflow_quality"));
    }

    @Test
    void omitsIndicatorsWithMissingInputsOrZeroDenominators() {
        Map<String, BigDecimal> current = values(
                "operating_revenue", "0",
                "operating_cost", "10",
                "net_profit", "5",
                "net_profit_parent", "5",
                "total_equity", "0",
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
import json
import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR / "docs"))
sys.path.insert(0, str(BACKEND_DIR / "sql"))

import fetch_real_data
import report_validator


class ResearchQualityTests(unittest.TestCase):
    def test_missing_financial_item_is_not_written_as_zero(self):
        rows = []
        missing = []

        fetch_real_data.append_report_item(
            rows, missing, 7, 2024, 2, None, "000001", "income", "operating_cost"
        )

        self.assertEqual([], rows)
        self.assertEqual([("000001", 2024, "income", "operating_cost")], missing)

    def test_actual_zero_financial_item_is_preserved(self):
        rows = []
        missing = []

        fetch_real_data.append_report_item(
            rows, missing, 7, 2024, 2, 0, "000001", "income", "operating_cost"
        )

        self.assertEqual([(7, 2024, 2, 0.0)], rows)
        self.assertEqual([], missing)

    def test_validator_matches_numbers_only_to_their_indicator(self):
        context = {
            "indicators": [
                {
                    "指标编码": "roe",
                    "指标名称": "ROE",
                    "公司值": 34.87,
                    "行业中位数": 20,
                    "行业排名": "1/8",
                },
                {"指标编码": "gross_margin", "指标名称": "毛利率", "公司值": 71.0},
            ]
        }

        result = report_validator.evaluate_answer(
            "ROE 34.87%，行业中位数20，排名1/8\n毛利率78%\n股票代码600519",
            json.dumps(context, ensure_ascii=False),
        )

        self.assertEqual(5, result["claims"])
        self.assertEqual(4, result["verified"])
        self.assertEqual([78.0], result["unverified"])
        self.assertEqual(1, result["unattributed"])

    def test_validator_handles_non_object_context(self):
        result = report_validator.evaluate_answer("ROE 34%", "[]")

        self.assertEqual(0, result["claims"])
        self.assertEqual(1, result["unattributed"])


if __name__ == "__main__":
    unittest.main()
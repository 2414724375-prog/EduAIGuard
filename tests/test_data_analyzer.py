from pathlib import Path
import unittest

from data_analyzer import analyze_survey_data, read_csv_flexible
from utils import DEFAULT_SURVEY_PATH


DATA_PATH = DEFAULT_SURVEY_PATH


class DataAnalyzerTests(unittest.TestCase):
    def test_read_csv_flexible_loads_local_survey(self):
        df = read_csv_flexible(DATA_PATH)

        self.assertEqual(len(df), 79)
        self.assertIn("3.学习中使用AI频率", df.columns)
        self.assertNotIn("IP", df.columns)
        self.assertNotIn("UA", df.columns)


    def test_analyze_survey_data_extracts_key_findings(self):
        df = read_csv_flexible(DATA_PATH)
        result = analyze_survey_data(df)

        self.assertEqual(result["sample_size"], 79)
        self.assertEqual(result["frequency_distribution"]["A.每天都用"], 61)
        self.assertEqual(result["ai_use_counts"]["查资料 / 解释概念"], 75)
        self.assertEqual(result["ai_use_counts"]["总结要点 / 列提纲"], 64)
        self.assertEqual(result["ai_use_counts"]["代码 / 公式推导辅助"], 56)
        self.assertEqual(result["ai_use_counts"]["其他"], 10)
        self.assertEqual(result["training_gap_combined"]["count"], 65)
        self.assertEqual(result["ddl_pressure_combined"]["count"], 63)

    def test_survey_options_follow_media_order_and_include_zero_values(self):
        df = read_csv_flexible(DATA_PATH)
        result = analyze_survey_data(df)

        self.assertEqual(
            list(result["ai_use_counts"].keys()),
            [
                "查资料 / 解释概念",
                "总结要点 / 列提纲",
                "润色改写表达",
                "生成作业 / 论文核心内容",
                "代码 / 公式推导辅助",
                "翻译/外语学习",
                "其他",
            ],
        )
        self.assertEqual(
            list(result["tool_distribution"].keys()),
            ["A.免费/基础款", "B.付费/进阶版", "C.不清楚", "D.多种类型混用"],
        )
        self.assertEqual(result["tool_distribution"]["C.不清楚"], 0)
        self.assertEqual(
            list(result["homework_acceptance"].keys()),
            [
                "查资料 / 解释概念",
                "总结要点 / 列提纲",
                "润色改写表达",
                "生成作业 / 论文核心内容",
                "代码 / 公式推导辅助",
                "翻译 / 外语学习",
            ],
        )


if __name__ == "__main__":
    unittest.main()

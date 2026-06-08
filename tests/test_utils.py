from pathlib import Path
import tempfile
import unittest

from utils import read_feedback_records, summarize_feedback


class FeedbackUtilsTests(unittest.TestCase):
    def test_feedback_summary_handles_empty_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "feedback.csv"
            path.write_text("提交时间,是否有帮助,最有用功能,是否愿意声明AI使用,开放建议\n", encoding="utf-8")

            records = read_feedback_records(path)
            summary = summarize_feedback(records)

        self.assertEqual(records, [])
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["helpfulness"], {})

    def test_feedback_summary_counts_populated_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "feedback.csv"
            path.write_text(
                "提交时间,是否有帮助,最有用功能,是否愿意声明AI使用,开放建议\n"
                "2026-06-04 10:00:00,很有帮助,风险评分,愿意,解释清楚\n"
                "2026-06-04 10:05:00,有一些帮助,AI 使用声明,看课程要求,希望加后台\n",
                encoding="utf-8",
            )

            records = read_feedback_records(path)
            summary = summarize_feedback(records)

        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["helpfulness"]["很有帮助"], 1)
        self.assertEqual(summary["useful_feature"]["风险评分"], 1)
        self.assertEqual(summary["willingness"]["看课程要求"], 1)


if __name__ == "__main__":
    unittest.main()

import unittest

from report_generator import generate_markdown_report
from rules import calculate_risk
from statement_generator import generate_statement


class ReportGeneratorTests(unittest.TestCase):
    def test_report_includes_enhanced_dimensions_and_checklist(self):
        user_input = {
            "assignment_type": "课程论文",
            "scenario": "普通作业",
            "teacher_rule": "允许但需要说明",
            "ai_uses": ["查资料 / 解释概念"],
            "uploaded_contents": ["普通题目要求"],
            "fact_check": "全部核查",
            "reference_check": "没有生成参考文献",
            "process_record": "保留完整草稿和修改记录",
            "disclosure": "主动声明",
            "time_pressure": "无明显时间压力",
            "training_gap": "没有",
            "tool_type": "免费 / 基础 AI 工具",
            "agency_level": "能独立解释核心思路",
            "material_authorization": "只使用普通题目或自有资料",
            "ethical_checks": [
                "我能独立解释作业的核心观点、代码或结论",
                "我已核查 AI 生成的事实、公式、代码和引用",
            ],
        }
        risk = calculate_risk(user_input)
        statement = generate_statement(user_input, risk)
        report = generate_markdown_report(user_input, risk, statement)

        self.assertIn("学习主体性风险", report)
        self.assertIn("责任证据风险", report)
        self.assertIn("版权授权风险", report)
        self.assertIn("伦理符合性自检", report)
        self.assertIn("我能独立解释作业的核心观点、代码或结论", report)


if __name__ == "__main__":
    unittest.main()

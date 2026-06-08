import os
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from app import _feedback_admin_password
from report_generator import generate_markdown_report
from rules import calculate_risk
from statement_generator import generate_statement


class StreamlitAppTests(unittest.TestCase):
    def test_feedback_admin_has_no_public_default_password(self):
        with patch.dict(os.environ, {"EDUAI_ADMIN_PASSWORD": ""}):
            self.assertEqual(_feedback_admin_password(), "")

        with patch.dict(os.environ, {"EDUAI_ADMIN_PASSWORD": "configured-secret"}):
            self.assertEqual(_feedback_admin_password(), "configured-secret")

    def test_all_sidebar_pages_render_without_exceptions(self):
        pages = [
            "首页",
            "调研数据概览",
            "AI 使用伦理自查",
            "AI 使用声明生成",
            "自查报告下载",
            "用户反馈",
            "项目说明",
        ]
        app = AppTest.from_file("app.py").run(timeout=20)

        for page in pages:
            app.radio[0].set_value(page).run(timeout=20)
            self.assertEqual(len(app.exception), 0, page)

    def test_completed_self_check_renders_without_progress_exception(self):
        user_input = {
            "assignment_type": "课程论文",
            "scenario": "普通作业",
            "teacher_rule": "允许但需要说明",
            "tool_type": "免费 / 基础 AI 工具",
            "ai_uses": ["查资料 / 解释概念"],
            "uploaded_contents": ["普通题目要求"],
            "fact_check": "全部核查",
            "reference_check": "没有生成参考文献",
            "process_record": "保留完整草稿和修改记录",
            "disclosure": "主动声明",
            "time_pressure": "无明显时间压力",
            "training_gap": "没有",
        }
        risk = calculate_risk(user_input)
        statement = generate_statement(user_input, risk)

        app = AppTest.from_file("app.py")
        app.session_state["wizard_step"] = 6
        app.session_state["last_user_input"] = user_input
        app.session_state["last_risk_result"] = risk
        app.session_state["last_statement"] = statement
        app.session_state["last_report"] = generate_markdown_report(user_input, risk, statement)

        app.run(timeout=20)
        app.radio[0].set_value("AI 使用伦理自查").run(timeout=20)

        self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()

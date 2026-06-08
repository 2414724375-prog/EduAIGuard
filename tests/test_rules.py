import unittest

from rules import calculate_risk


class RiskRuleTests(unittest.TestCase):
    def test_low_risk_helper_usage_stays_low(self):
        result = calculate_risk(
            {
                "assignment_type": "课程论文",
                "scenario": "普通作业",
                "teacher_rule": "允许但需要说明",
                "ai_uses": ["查资料 / 解释概念", "总结要点 / 列提纲", "润色改写表达"],
                "uploaded_contents": ["普通题目要求", "自己的草稿"],
                "fact_check": "全部核查",
                "reference_check": "没有生成参考文献",
                "process_record": "保留完整草稿和修改记录",
                "disclosure": "主动声明",
                "time_pressure": "无明显时间压力",
                "training_gap": "没有",
                "tool_type": "免费 / 基础 AI 工具",
            }
        )

        self.assertEqual(result["final_level"], "低风险")
        self.assertLessEqual(result["final_score"], 25)

    def test_generated_experiment_data_forces_serious_risk(self):
        result = calculate_risk(
            {
                "assignment_type": "实验报告",
                "scenario": "科研训练",
                "teacher_rule": "没有说明",
                "ai_uses": ["生成实验数据"],
                "uploaded_contents": ["自己的实验数据"],
                "fact_check": "部分核查",
                "reference_check": "没有生成参考文献",
                "process_record": "没有保留",
                "disclosure": "不确定",
                "time_pressure": "有一些时间压力",
                "training_gap": "有一些",
                "tool_type": "多种类型混用",
            }
        )

        self.assertEqual(result["final_level"], "严重风险")
        self.assertGreaterEqual(result["dimension_scores"]["academic_integrity"], 90)
        self.assertGreaterEqual(result["dimension_scores"]["reliability"], 90)
        self.assertIn("生成实验数据", " ".join(result["triggered_rules"]))

    def test_core_content_without_disclosure_forces_serious_risk(self):
        result = calculate_risk(
            {
                "assignment_type": "课程论文",
                "scenario": "课程论文",
                "teacher_rule": "没有说明",
                "ai_uses": ["生成作业 / 论文核心内容"],
                "uploaded_contents": ["普通题目要求"],
                "fact_check": "部分核查",
                "reference_check": "没有生成参考文献",
                "process_record": "保留部分记录",
                "disclosure": "不打算声明",
                "time_pressure": "DDL 临近，主要靠 AI 救火",
                "training_gap": "明显超过课堂训练",
                "tool_type": "付费 / 进阶 AI 工具",
            }
        )

        self.assertEqual(result["final_level"], "严重风险")
        self.assertGreaterEqual(result["dimension_scores"]["transparency"], 90)

    def test_exam_substantive_ai_use_forces_serious_risk(self):
        result = calculate_risk(
            {
                "assignment_type": "考试复习",
                "scenario": "考试 / 测验",
                "teacher_rule": "不确定",
                "ai_uses": ["代码 / 公式推导辅助"],
                "uploaded_contents": ["普通题目要求"],
                "fact_check": "基本未核查",
                "reference_check": "没有生成参考文献",
                "process_record": "没有保留",
                "disclosure": "不确定",
                "time_pressure": "有一些时间压力",
                "training_gap": "有一些",
                "tool_type": "免费 / 基础 AI 工具",
            }
        )

        self.assertEqual(result["final_level"], "严重风险")
        self.assertTrue(any("考试" in item for item in result["triggered_rules"]))

    def test_enhanced_profile_includes_eight_dimensions(self):
        result = calculate_risk(
            {
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
                    "我没有让 AI 编造实验数据、访谈数据或问卷数据",
                    "我没有上传同学作业、聊天记录、个人身份信息",
                    "我已核查 AI 生成的事实、公式、代码和引用",
                    "我保留了草稿、修改过程或关键 prompt",
                    "如果课程要求，我会主动声明 AI 使用",
                ],
            }
        )

        self.assertEqual(len(result["dimension_scores"]), 8)
        self.assertIn("learning_agency", result["dimension_scores"])
        self.assertIn("accountability", result["dimension_scores"])
        self.assertIn("copyright", result["dimension_scores"])

    def test_unlicensed_material_raises_copyright_risk(self):
        result = calculate_risk(
            {
                "assignment_type": "课程论文",
                "scenario": "普通作业",
                "teacher_rule": "没有说明",
                "ai_uses": ["总结要点 / 列提纲"],
                "uploaded_contents": ["课程 PPT / 讲义"],
                "fact_check": "全部核查",
                "reference_check": "没有生成参考文献",
                "process_record": "保留部分记录",
                "disclosure": "主动声明",
                "time_pressure": "无明显时间压力",
                "training_gap": "没有",
                "tool_type": "免费 / 基础 AI 工具",
                "agency_level": "能独立解释核心思路",
                "material_authorization": "上传未授权教材/论文/图片",
                "ethical_checks": [],
            }
        )

        self.assertGreaterEqual(result["dimension_scores"]["copyright"], 70)
        self.assertTrue(any("版权" in item or "授权" in item for item in result["explanations"]))

    def test_direct_copy_ai_output_raises_learning_agency_risk(self):
        result = calculate_risk(
            {
                "assignment_type": "课程论文",
                "scenario": "课程论文",
                "teacher_rule": "没有说明",
                "ai_uses": ["生成部分段落"],
                "uploaded_contents": ["普通题目要求"],
                "fact_check": "部分核查",
                "reference_check": "没有生成参考文献",
                "process_record": "没有保留",
                "disclosure": "不确定",
                "time_pressure": "有一些时间压力",
                "training_gap": "有一些",
                "tool_type": "免费 / 基础 AI 工具",
                "agency_level": "直接复制 AI 输出",
                "material_authorization": "只使用普通题目或自有资料",
                "ethical_checks": [],
            }
        )

        self.assertGreaterEqual(result["dimension_scores"]["learning_agency"], 90)
        self.assertIn(result["final_level"], {"高风险", "严重风险"})
        self.assertTrue(any("主体" in item or "复制" in item for item in result["explanations"]))


if __name__ == "__main__":
    unittest.main()

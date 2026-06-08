"""Markdown report generation for EduAI-Guard."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable


def generate_markdown_report(
    user_input: Dict[str, Any],
    risk_result: Dict[str, Any],
    statement: str,
) -> str:
    """Generate a complete Markdown AI ethics self-check report."""

    scores = risk_result.get("dimension_scores", {})
    labels = risk_result.get("dimension_labels", {})
    lines = [
        "# AI 使用伦理自查报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 1. 基本信息",
        f"- 作业类型：{user_input.get('assignment_type', '未填写')}",
        f"- 使用场景：{user_input.get('scenario', '未填写')}",
        f"- 教师 AI 使用规则：{user_input.get('teacher_rule', '未填写')}",
        f"- 时间压力：{user_input.get('time_pressure', '未填写')}",
        f"- 作业是否超过课堂训练：{user_input.get('training_gap', '未填写')}",
        "",
        "## 2. AI 使用方式",
        _bullet_list(user_input.get("ai_uses", [])),
        "",
        "## 3. 数据上传情况",
        _bullet_list(user_input.get("uploaded_contents", [])),
        f"- 资料授权情况：{user_input.get('material_authorization', '未填写')}",
        "",
        "## 4. 核查、主体性与证据",
        f"- 学习主体性判断：{user_input.get('agency_level', '未填写')}",
        f"- 事实核查情况：{user_input.get('fact_check', '未填写')}",
        f"- 参考文献核查：{user_input.get('reference_check', '未填写')}",
        f"- 过程证据留存：{user_input.get('process_record', '未填写')}",
        "",
        "## 5. 伦理符合性自检",
        _bullet_list(user_input.get("ethical_checks", [])),
        "",
        "## 6. 风险评估结果",
        f"- 综合风险等级：{risk_result.get('final_level', '未计算')}",
        f"- 综合风险分数：{risk_result.get('final_score', '未计算')}",
    ]

    for key, value in scores.items():
        label = labels.get(key, key)
        lines.append(f"- {label}：{value}")

    checklist = risk_result.get("ethical_checklist", {})
    if checklist:
        lines.append(
            f"- 伦理自检完成度：{checklist.get('passed', 0)}/{checklist.get('total', 0)}"
        )

    lines.extend(
        [
            "",
            "## 7. 主要风险解释",
            _bullet_list(risk_result.get("explanations", [])),
            "",
            "## 8. 修改建议",
            _bullet_list(risk_result.get("suggestions", [])),
            "",
            "## 9. AI 使用声明",
            statement,
            "",
            "## 10. 触发的特殊规则",
            _bullet_list(risk_result.get("triggered_rules", [])),
            "",
            "## 11. 责任提醒",
            "本报告仅作为 AI 使用伦理自查参考，不能替代学校、学院或任课教师的正式规定。最终提交内容的真实性、原创性、授权合规性、人工核查和透明披露责任由提交者本人负责。",
            "",
        ]
    )
    return "\n".join(lines)


def _bullet_list(items: Iterable[Any]) -> str:
    values = [str(item) for item in items if str(item).strip()]
    if not values:
        return "- 无"
    return "\n".join(f"- {item}" for item in values)

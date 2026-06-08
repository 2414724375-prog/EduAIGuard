"""AI usage statement generation for EduAI-Guard."""

from __future__ import annotations

from typing import Any, Dict, List


def generate_statement(user_input: Dict[str, Any], risk_result: Dict[str, Any]) -> str:
    """Generate a Chinese AI usage statement based on use pattern and risk."""

    ai_uses = _as_list(user_input.get("ai_uses"))
    assignment_type = str(user_input.get("assignment_type", "本作业"))
    scenario = str(user_input.get("scenario", ""))
    teacher_rule = str(user_input.get("teacher_rule", ""))
    final_level = str(risk_result.get("final_level", "中风险"))

    if teacher_rule == "明确禁止" or (
        scenario == "考试 / 测验" and final_level == "严重风险"
    ):
        return (
            "当前情况可能违反课程、考试或教师要求。建议停止使用 AI 完成该任务，"
            "并遵守学校、学院或任课教师的正式规定。"
        )

    if "代码作业" in assignment_type or "代码 / 公式推导辅助" in ai_uses:
        return (
            "本作业在完成过程中使用生成式人工智能工具辅助理解报错信息、梳理代码思路"
            "或优化代码表达。核心算法思路、代码实现和调试结果由作者独立完成，"
            "作者已对 AI 建议内容进行检查和修改。"
        )

    if final_level in {"高风险", "严重风险"} or _has_core_generation(ai_uses):
        return (
            "根据当前填写的信息，AI 已经较深参与作业核心内容生成。建议在提交前"
            "重新完成核心分析、论证和结论，并根据课程要求如实说明 AI 使用范围。"
            "当前内容不建议直接作为合规声明使用。"
        )

    if final_level == "中风险":
        return (
            "本文在完成过程中使用生成式人工智能工具辅助进行资料整理、提纲生成、"
            "语言润色和部分内容优化。作者未直接采用 AI 生成的完整文本，而是在此"
            "基础上进行了独立分析、内容重构和事实核查。文中核心观点和结论由作者"
            "独立完成。"
        )

    return (
        "本文在完成过程中使用生成式人工智能工具辅助进行资料检索、概念理解、"
        "语言润色或表达优化。本文的选题、结构设计、核心观点、论证过程和结论"
        "均由作者独立完成。作者已对 AI 辅助生成或修改的内容进行核查和修订。"
    )


def _has_core_generation(ai_uses: List[str]) -> bool:
    return bool(
        {
            "生成作业 / 论文核心内容",
            "生成实验数据",
            "代写核心分析与结论",
        }.intersection(ai_uses)
    )


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []

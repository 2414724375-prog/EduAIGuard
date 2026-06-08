"""Ethical risk rules for EduAI-Guard.

The module intentionally uses a transparent rule table instead of a model call.
This makes each risk score traceable for course documentation and classroom use.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


DIMENSION_LABELS = {
    "academic_integrity": "学术诚信风险",
    "data_privacy": "数据隐私风险",
    "reliability": "内容可靠性风险",
    "fairness": "偏见与公平风险",
    "transparency": "透明披露风险",
    "learning_agency": "学习主体性风险",
    "accountability": "责任证据风险",
    "copyright": "版权授权风险",
}

LEVEL_BANDS: List[Tuple[int, int, str]] = [
    (0, 25, "低风险"),
    (26, 50, "中风险"),
    (51, 75, "高风险"),
    (76, 100, "严重风险"),
]

ACADEMIC_RULES = {
    "查资料 / 解释概念": 10,
    "总结要点 / 列提纲": 15,
    "润色改写表达": 15,
    "翻译 / 外语学习": 10,
    "翻译/外语学习": 10,
    "代码 / 公式推导辅助": 25,
    "生成部分段落": 45,
    "生成作业 / 论文核心内容": 75,
    "生成参考文献": 50,
    "生成实验数据": 90,
    "代写核心分析与结论": 90,
}

PRIVACY_RULES = {
    "未上传资料": 0,
    "普通题目要求": 5,
    "课程 PPT / 讲义": 20,
    "自己的草稿": 10,
    "自己的实验数据": 25,
    "同学作业 / 同学资料": 70,
    "聊天记录": 70,
    "个人身份信息": 85,
    "未公开研究材料": 80,
}

FACT_CHECK_RULES = {
    "全部核查": 0,
    "部分核查": 30,
    "基本未核查": 70,
    "不确定": 50,
}

REFERENCE_RULES = {
    "没有生成参考文献": 0,
    "已逐条核查": 0,
    "只核查部分": 30,
    "未核查": 55,
    "AI 生成了不存在的参考文献但我还没处理": 85,
}

TOOL_FAIRNESS_RULES = {
    "免费 / 基础 AI 工具": 15,
    "免费/基础款": 15,
    "A.免费/基础款": 15,
    "付费 / 进阶 AI 工具": 20,
    "付费/进阶版": 20,
    "B.付费/进阶版": 20,
    "多种类型混用": 25,
    "D.多种类型混用": 25,
}

DISCLOSURE_RULES = {
    "主动声明": 0,
    "按教师要求声明": 5,
    "不确定": 35,
    "不打算声明": 70,
}

AGENCY_RULES = {
    "能独立解释核心思路": 0,
    "需要参考 AI 才能解释": 30,
    "基本无法脱离 AI 解释": 70,
    "直接复制 AI 输出": 90,
}

PROCESS_RECORD_RULES = {
    "保留完整草稿和修改记录": 0,
    "保留部分记录": 20,
    "没有保留": 65,
    "不确定": 45,
}

AUTHORIZATION_RULES = {
    "只使用普通题目或自有资料": 0,
    "使用课程资料但仅用于理解": 15,
    "上传未授权教材/论文/图片": 75,
    "上传同学作品或未公开材料": 85,
    "不确定资料授权": 45,
}

ETHICAL_CHECKS = [
    "我能独立解释作业的核心观点、代码或结论",
    "我没有让 AI 编造实验数据、访谈数据或问卷数据",
    "我没有上传同学作业、聊天记录、个人身份信息",
    "我已核查 AI 生成的事实、公式、代码和引用",
    "我保留了草稿、修改过程或关键 prompt",
    "如果课程要求，我会主动声明 AI 使用",
]

LOW_RISK_USES = {
    "查资料 / 解释概念",
    "总结要点 / 列提纲",
    "润色改写表达",
    "翻译 / 外语学习",
    "翻译/外语学习",
}

SUBSTANTIVE_EXAM_USES = {
    "生成作业 / 论文核心内容",
    "代码 / 公式推导辅助",
    "生成参考文献",
    "生成实验数据",
    "代写核心分析与结论",
}


def calculate_risk(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate five-dimensional ethical risk for a student's AI usage."""

    ai_uses = _as_list(user_input.get("ai_uses"))
    uploaded_contents = _as_list(user_input.get("uploaded_contents"))
    scenario = str(user_input.get("scenario", ""))
    teacher_rule = str(user_input.get("teacher_rule", ""))
    fact_check = str(user_input.get("fact_check", "不确定"))
    reference_check = str(user_input.get("reference_check", "没有生成参考文献"))
    process_record = str(user_input.get("process_record", "不确定"))
    disclosure = str(user_input.get("disclosure", "不确定"))
    time_pressure = str(user_input.get("time_pressure", "无明显时间压力"))
    training_gap = str(user_input.get("training_gap", "没有"))
    tool_type = str(user_input.get("tool_type", "免费 / 基础 AI 工具"))
    agency_level = str(user_input.get("agency_level", "能独立解释核心思路"))
    material_authorization = str(user_input.get("material_authorization", "只使用普通题目或自有资料"))
    ethical_checks = set(_as_list(user_input.get("ethical_checks")))

    scores = {
        "academic_integrity": 0,
        "data_privacy": 0,
        "reliability": 0,
        "fairness": 0,
        "transparency": 0,
        "learning_agency": 0,
        "accountability": 0,
        "copyright": 0,
    }
    explanations: List[str] = []
    suggestions: List[str] = []
    triggered_rules: List[str] = []
    serious_override = False
    high_minimum = False

    for use in ai_uses:
        scores["academic_integrity"] += ACADEMIC_RULES.get(use, 10)
        explanation = _use_explanation(use)
        if explanation:
            explanations.append(explanation)

    for content in uploaded_contents:
        scores["data_privacy"] += PRIVACY_RULES.get(content, 10)
        if content in {"同学作业 / 同学资料", "聊天记录", "个人身份信息", "未公开研究材料"}:
            explanations.append(f"上传“{content}”存在较高隐私、授权或数据伦理风险。")
            suggestions.append("不要上传同学作业、聊天记录、个人身份信息和未公开研究材料。")

    scores["reliability"] += FACT_CHECK_RULES.get(fact_check, 50)
    scores["reliability"] += REFERENCE_RULES.get(reference_check, 0)
    if fact_check in {"部分核查", "基本未核查", "不确定"}:
        explanations.append("AI 输出存在事实错误、遗漏背景或误导性表达的可能，需要人工核查。")
        suggestions.append("对 AI 生成的事实、数据、公式、代码和结论逐项核查。")

    if "生成参考文献" in ai_uses and reference_check in {"未核查", "只核查部分"}:
        scores["reliability"] += 40
        explanations.append("生成式 AI 可能编造不存在的参考文献，未核查会显著增加可靠性风险。")
        suggestions.append("删除无法核实的参考文献，改用知网、Google Scholar、Web of Science 等数据库核查真实文献。")

    if reference_check == "AI 生成了不存在的参考文献但我还没处理":
        scores["reliability"] = max(scores["reliability"], 85)
        triggered_rules.append("存在 AI 编造参考文献且尚未处理，内容可靠性风险不低于 85。")

    scores["fairness"] += TOOL_FAIRNESS_RULES.get(tool_type, 15)
    if time_pressure == "DDL 临近，主要靠 AI 救火":
        scores["fairness"] += 35
        explanations.append("DDL 临近时主要依赖 AI，容易从辅助学习滑向替代性完成任务。")
        suggestions.append("将 AI 用于拆解任务和检查表达，核心分析与结论仍应由自己完成。")
    elif time_pressure == "有一些时间压力":
        scores["fairness"] += 15

    if training_gap == "明显超过课堂训练":
        scores["fairness"] += 35
        explanations.append("作业明显超过课堂训练时，学生可能因能力差距或资源差异而更依赖 AI。")
        suggestions.append("遇到明显超出课堂训练的任务，应优先向教师或助教确认要求。")
    elif training_gap == "有一些":
        scores["fairness"] += 15

    if "生成作业 / 论文核心内容" in ai_uses:
        scores["fairness"] += 35
    if "代码 / 公式推导辅助" in ai_uses:
        scores["fairness"] += 20
    if scenario == "考试 / 测验" and ai_uses:
        scores["fairness"] += 50

    scores["transparency"] += DISCLOSURE_RULES.get(disclosure, 35)
    if disclosure in {"不打算声明", "不确定"}:
        explanations.append("未声明或不确定是否声明 AI 使用，会削弱透明性和责任追溯。")
        suggestions.append("在作业末尾添加 AI 使用声明，说明工具参与的环节和人工核查责任。")

    scores["accountability"] += PROCESS_RECORD_RULES.get(process_record, 45)
    if process_record in {"没有保留", "不确定"}:
        scores["academic_integrity"] += 10
        scores["transparency"] += 10
        suggestions.append("保留原始草稿、修改记录和关键思考过程，以便说明 AI 只是辅助工具。")

    scores["learning_agency"] += AGENCY_RULES.get(agency_level, 30)
    if agency_level == "需要参考 AI 才能解释":
        explanations.append("需要参考 AI 才能解释核心思路，说明学习主体性存在一定弱化。")
        suggestions.append("在提交前用自己的话复述核心观点、代码逻辑或推导过程。")
    elif agency_level == "基本无法脱离 AI 解释":
        explanations.append("基本无法脱离 AI 解释核心内容，说明 AI 可能已经替代个人理解过程。")
        suggestions.append("重新梳理核心论证和关键步骤，确保自己能够独立说明。")
    elif agency_level == "直接复制 AI 输出":
        scores["academic_integrity"] += 35
        explanations.append("直接复制 AI 输出会严重削弱学习主体性，并可能构成替代性完成。")
        suggestions.append("不要直接复制 AI 输出，应重写、核查并补充个人判断。")
        triggered_rules.append("直接复制 AI 输出，综合风险至少为高风险。")
        high_minimum = True

    scores["copyright"] += AUTHORIZATION_RULES.get(material_authorization, 45)
    if material_authorization in {"上传未授权教材/论文/图片", "上传同学作品或未公开材料", "不确定资料授权"}:
        explanations.append("上传或使用授权不明确的教材、论文、图片、同学作品或未公开材料，存在版权授权风险。")
        suggestions.append("仅上传自己有权使用的资料；涉及教材、论文、图片和同学作品时应确认授权或改用摘要描述。")
    if material_authorization == "上传同学作品或未公开材料":
        scores["data_privacy"] += 25
        triggered_rules.append("上传同学作品或未公开材料，版权授权与隐私风险较高。")
        high_minimum = True

    _apply_ethical_checklist_adjustments(ethical_checks, scores, explanations, suggestions)

    if "生成实验数据" in ai_uses:
        scores["academic_integrity"] = max(scores["academic_integrity"], 90)
        scores["reliability"] = max(scores["reliability"], 90)
        explanations.append("生成实验数据属于严重风险，可能构成数据造假。")
        suggestions.append("不得用 AI 生成、替换或伪造实验数据，应保留真实实验记录。")
        triggered_rules.append("选择了生成实验数据，综合风险设为严重风险。")
        serious_override = True

    if "生成作业 / 论文核心内容" in ai_uses:
        explanations.append("AI 生成作业或论文核心内容可能替代学生本应完成的核心思考和写作过程。")
        suggestions.append("将 AI 生成全文或核心内容改为只用于提纲参考、资料提示或语言润色。")
        if disclosure == "不打算声明":
            scores["transparency"] = max(scores["transparency"], 90)
            triggered_rules.append("生成作业/论文核心内容且不打算声明，综合风险设为严重风险。")
            serious_override = True

    if "代写核心分析与结论" in ai_uses:
        explanations.append("代写核心分析与结论属于严重学术诚信风险。")
        suggestions.append("论文或报告的核心观点、分析框架和结论应由学生自己完成。")
        serious_override = True

    if teacher_rule == "明确禁止" and ai_uses:
        scores["transparency"] = max(scores["transparency"], 90)
        explanations.append("教师已明确禁止使用 AI，继续使用可能违反课程要求。")
        suggestions.append("如果教师明确禁止使用 AI，应遵守课程要求并停止在该任务中使用 AI。")
        triggered_rules.append("教师明确禁止 AI 但仍使用，综合风险至少为高风险。")
        high_minimum = True

    if scenario == "考试 / 测验" and SUBSTANTIVE_EXAM_USES.intersection(ai_uses):
        explanations.append("考试或测验场景中使用 AI 完成实质任务可能破坏评价公平。")
        suggestions.append("考试场景不应使用 AI 完成答题、推导、代码或核心内容生成任务。")
        triggered_rules.append("考试/测验场景中使用 AI 完成实质任务，综合风险设为严重风险。")
        serious_override = True

    _add_default_suggestions(ai_uses, suggestions)
    scores = {key: min(100, max(0, value)) for key, value in scores.items()}

    if _is_benign_low_risk_case(
        ai_uses,
        fact_check,
        reference_check,
        disclosure,
        teacher_rule,
        time_pressure,
        training_gap,
        agency_level,
        material_authorization,
    ):
        for key in scores:
            scores[key] = min(scores[key], 25)
        triggered_rules.append("仅使用低风险辅助功能并完成核查与声明，综合风险可判定为低风险。")

    final_score = _combined_score(scores)
    if serious_override:
        final_score = max(final_score, 85)
    if high_minimum:
        final_score = max(final_score, 51)

    final_score = min(100, round(final_score, 1))
    final_level = _score_to_level(final_score)
    if serious_override:
        final_level = "严重风险"
    elif high_minimum and final_level in {"低风险", "中风险"}:
        final_level = "高风险"

    return {
        "dimension_scores": scores,
        "dimension_labels": DIMENSION_LABELS,
        "final_score": final_score,
        "final_level": final_level,
        "level_description": _level_description(final_level),
        "explanations": _dedupe(explanations),
        "suggestions": _dedupe(suggestions),
        "triggered_rules": _dedupe(triggered_rules),
        "ethical_checklist": _ethical_checklist_summary(ethical_checks),
    }


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple) or isinstance(value, set):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _combined_score(scores: Dict[str, int]) -> float:
    values = list(scores.values())
    max_score = max(values) if values else 0
    avg_score = sum(values) / len(values) if values else 0
    return max_score * 0.7 + avg_score * 0.3


def _score_to_level(score: float) -> str:
    for low, high, level in LEVEL_BANDS:
        if low <= score <= high:
            return level
    return "严重风险"


def _level_description(level: str) -> str:
    descriptions = {
        "低风险": "AI 主要用于非核心辅助，仍需保留人工核查和必要声明。",
        "中风险": "AI 已参与部分学习或表达过程，需要补充个人判断、核查和透明说明。",
        "高风险": "AI 可能替代核心任务或涉及隐私、可靠性、披露问题，提交前应明显调整。",
        "严重风险": "当前行为可能涉及学术不端、数据造假、考试违规或严重隐私风险，不建议直接提交。",
    }
    return descriptions.get(level, "")


def _use_explanation(use: str) -> str:
    mapping = {
        "查资料 / 解释概念": "查资料或解释概念通常属于较低风险学习辅助，但仍需要核查 AI 解释是否准确。",
        "总结要点 / 列提纲": "总结要点或列提纲可以帮助整理思路，但不能替代学生自己的结构设计和核心论证。",
        "润色改写表达": "润色改写属于表达层面的辅助，需要避免 AI 改写改变原意。",
        "翻译 / 外语学习": "翻译或外语学习通常风险较低，但需要确认专业术语和语义没有偏差。",
        "翻译/外语学习": "翻译或外语学习通常风险较低，但需要确认专业术语和语义没有偏差。",
        "代码 / 公式推导辅助": "代码或公式推导辅助存在中等风险，学生需要理解代码逻辑和推导过程。",
        "生成部分段落": "生成部分段落会增加学术诚信风险，应进行重写、核查并说明 AI 参与范围。",
        "生成参考文献": "生成参考文献存在较高可靠性风险，因为生成式 AI 可能编造不存在的文献。",
    }
    return mapping.get(use, "")


def _is_benign_low_risk_case(
    ai_uses: List[str],
    fact_check: str,
    reference_check: str,
    disclosure: str,
    teacher_rule: str,
    time_pressure: str,
    training_gap: str,
    agency_level: str,
    material_authorization: str,
) -> bool:
    if not ai_uses:
        return True
    return (
        set(ai_uses).issubset(LOW_RISK_USES)
        and fact_check == "全部核查"
        and reference_check in {"没有生成参考文献", "已逐条核查"}
        and disclosure in {"主动声明", "按教师要求声明"}
        and teacher_rule != "明确禁止"
        and time_pressure != "DDL 临近，主要靠 AI 救火"
        and training_gap != "明显超过课堂训练"
        and agency_level == "能独立解释核心思路"
        and material_authorization in {"只使用普通题目或自有资料", "使用课程资料但仅用于理解"}
    )


def _apply_ethical_checklist_adjustments(
    ethical_checks: set[str],
    scores: Dict[str, int],
    explanations: List[str],
    suggestions: List[str],
) -> None:
    if not ethical_checks:
        scores["accountability"] += 15
        suggestions.append("建议完成伦理符合性自检清单，确认主体性、核查、授权和披露责任。")
        return

    missing = set(ETHICAL_CHECKS) - ethical_checks
    if "我能独立解释作业的核心观点、代码或结论" in missing:
        scores["learning_agency"] += 20
        suggestions.append("补充个人复述和解释，确认自己能独立说明作业核心内容。")
    if "我没有让 AI 编造实验数据、访谈数据或问卷数据" in missing:
        scores["academic_integrity"] += 15
        scores["reliability"] += 15
        explanations.append("未确认数据未由 AI 编造，会增加学术诚信和内容可靠性风险。")
    if "我没有上传同学作业、聊天记录、个人身份信息" in missing:
        scores["data_privacy"] += 15
        suggestions.append("再次确认未上传同学作业、聊天记录和个人身份信息。")
    if "我已核查 AI 生成的事实、公式、代码和引用" in missing:
        scores["reliability"] += 15
        suggestions.append("对 AI 生成的事实、公式、代码和引用补充人工核查。")
    if "我保留了草稿、修改过程或关键 prompt" in missing:
        scores["accountability"] += 15
        suggestions.append("保留关键 prompt、草稿和修改记录，便于说明 AI 参与范围。")
    if "如果课程要求，我会主动声明 AI 使用" in missing:
        scores["transparency"] += 15
        suggestions.append("根据课程要求主动声明 AI 使用，避免透明披露不足。")


def _ethical_checklist_summary(ethical_checks: set[str]) -> Dict[str, Any]:
    selected = [item for item in ETHICAL_CHECKS if item in ethical_checks]
    missing = [item for item in ETHICAL_CHECKS if item not in ethical_checks]
    return {
        "selected": selected,
        "missing": missing,
        "passed": len(selected),
        "total": len(ETHICAL_CHECKS),
    }


def _add_default_suggestions(ai_uses: List[str], suggestions: List[str]) -> None:
    if "代码 / 公式推导辅助" in ai_uses:
        suggestions.append("对代码作业，必须理解每一行代码的功能和整体算法逻辑。")
    if "生成参考文献" in ai_uses:
        suggestions.append("参考文献必须逐条核查真实来源、作者、标题、期刊和年份。")
    suggestions.append("最终提交内容的真实性、原创性和合规性由提交者本人负责。")


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result


if __name__ == "__main__":
    sample = {
        "assignment_type": "课程论文",
        "scenario": "普通作业",
        "teacher_rule": "允许但需要说明",
        "ai_uses": ["查资料 / 解释概念", "润色改写表达"],
        "uploaded_contents": ["普通题目要求"],
        "fact_check": "全部核查",
        "reference_check": "没有生成参考文献",
        "process_record": "保留完整草稿和修改记录",
        "disclosure": "主动声明",
        "time_pressure": "无明显时间压力",
        "training_gap": "没有",
        "tool_type": "免费 / 基础 AI 工具",
    }
    print(calculate_risk(sample))

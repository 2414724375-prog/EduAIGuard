"""Survey data loading and analysis helpers for EduAI-Guard."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

try:
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal envs
    pd = None


ENCODINGS = ("utf-8-sig", "utf-8", "gbk")

FREQUENCY_FIELD = "3.学习中使用AI频率"
TOOL_FIELD = "8.你主要使用的AI工具类型属于哪种"
TOOL_IMPACT_FIELD = "9.你认为工具强弱差异对作业/论文质量或者成绩的影响"
TRAINING_GAP_FIELD = "10.你是否遇到过“作业/论文要求超过课堂训练实例”的情况"
DDL_FIELD = "11.你是否遇到过DDL迫在眉睫，时间不够，只能用AI救火"

AI_USE_PREFIX = "4.用AI做什么:"
HOMEWORK_PREFIX = "5.作业场景下AI用法接受度:"
PAPER_PREFIX = "6.论文场景:"
EXAM_PREFIX = "7.考试场景下AI用法接受度:"

FREQUENCY_OPTIONS = ["A.每天都用", "B.每周3~5次", "C.每周1~2次", "D.几乎不用"]
AI_USE_OPTIONS = [
    "查资料 / 解释概念",
    "总结要点 / 列提纲",
    "润色改写表达",
    "生成作业 / 论文核心内容",
    "代码 / 公式推导辅助",
    "翻译/外语学习",
    "其他",
]
ACCEPTANCE_USE_OPTIONS = [
    "查资料 / 解释概念",
    "总结要点 / 列提纲",
    "润色改写表达",
    "生成作业 / 论文核心内容",
    "代码 / 公式推导辅助",
    "翻译 / 外语学习",
]
TOOL_OPTIONS = ["A.免费/基础款", "B.付费/进阶版", "C.不清楚", "D.多种类型混用"]
TOOL_IMPACT_OPTIONS = ["A.影响很大", "B.有一些影响", "C.不影响", "D.不确定"]
TRAINING_GAP_OPTIONS = ["A.经常", "B.偶尔", "C.很少", "D.从不"]
DDL_OPTIONS = ["A.经常", "B.偶尔", "C.很少", "D.从不"]


@dataclass
class SimpleDataFrame:
    """Small dataframe-like fallback used when pandas is unavailable."""

    rows: List[Dict[str, str]]
    columns: List[str]

    def __len__(self) -> int:
        return len(self.rows)

    def to_dict(self, orient: str = "records") -> List[Dict[str, str]]:
        if orient != "records":
            raise ValueError("SimpleDataFrame only supports orient='records'")
        return self.rows


def read_csv_flexible(source: Any) -> Any:
    """Read a CSV path or uploaded file with common Chinese encodings."""

    if hasattr(source, "read"):
        raw = source.read()
        if hasattr(source, "seek"):
            source.seek(0)
        if isinstance(raw, str):
            raw_bytes = raw.encode("utf-8")
        else:
            raw_bytes = raw
        for encoding in ENCODINGS:
            try:
                text = raw_bytes.decode(encoding)
                return _read_csv_text(text)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("csv", raw_bytes, 0, 1, "无法识别 CSV 编码")

    path = Path(source)
    for encoding in ENCODINGS:
        try:
            text = path.read_text(encoding=encoding)
            return _read_csv_text(text)
        except UnicodeDecodeError:
            continue
    text = path.read_text(encoding="utf-8", errors="replace")
    return _read_csv_text(text)


def analyze_survey_data(df: Any) -> Dict[str, Any]:
    """Return structured survey statistics used by the Streamlit page and docs."""

    rows, columns = _records_and_columns(df)
    sample_size = len(rows)
    missing_fields: List[str] = []

    def require(field: str) -> bool:
        if field not in columns:
            missing_fields.append(field)
            return False
        return True

    result: Dict[str, Any] = {
        "sample_size": sample_size,
        "missing_fields": missing_fields,
        "frequency_distribution": {},
        "ai_use_counts": {},
        "ai_use_rates": {},
        "homework_acceptance": {},
        "paper_acceptance": {},
        "exam_acceptance": {},
        "tool_distribution": {},
        "tool_impact_distribution": {},
        "training_gap_distribution": {},
        "ddl_pressure_distribution": {},
        "training_gap_combined": {"count": 0, "rate": 0.0},
        "ddl_pressure_combined": {"count": 0, "rate": 0.0},
        "insights": [],
    }

    if require(FREQUENCY_FIELD):
        result["frequency_distribution"] = _ordered_counts(value_counts(rows, FREQUENCY_FIELD), FREQUENCY_OPTIONS)

    ai_use_fields = [field for field in columns if field.startswith(AI_USE_PREFIX)]
    ai_counts = selection_counts(rows, ai_use_fields, AI_USE_PREFIX, AI_USE_OPTIONS)
    result["ai_use_counts"] = ai_counts
    result["ai_use_rates"] = _rates(ai_counts, sample_size)

    result["homework_acceptance"] = acceptance_stats(rows, columns, HOMEWORK_PREFIX)
    result["paper_acceptance"] = acceptance_stats(rows, columns, PAPER_PREFIX)
    result["exam_acceptance"] = acceptance_stats(rows, columns, EXAM_PREFIX)

    if require(TOOL_FIELD):
        result["tool_distribution"] = _ordered_counts(value_counts(rows, TOOL_FIELD), TOOL_OPTIONS)
    if require(TOOL_IMPACT_FIELD):
        result["tool_impact_distribution"] = _ordered_counts(value_counts(rows, TOOL_IMPACT_FIELD), TOOL_IMPACT_OPTIONS)
    if require(TRAINING_GAP_FIELD):
        training = _ordered_counts(value_counts(rows, TRAINING_GAP_FIELD), TRAINING_GAP_OPTIONS)
        result["training_gap_distribution"] = training
        result["training_gap_combined"] = _combined_count(training, ("A.经常", "B.偶尔"), sample_size)
    if require(DDL_FIELD):
        ddl = _ordered_counts(value_counts(rows, DDL_FIELD), DDL_OPTIONS)
        result["ddl_pressure_distribution"] = ddl
        result["ddl_pressure_combined"] = _combined_count(ddl, ("A.经常", "B.偶尔"), sample_size)

    result["insights"] = build_insights(result)
    return result


def value_counts(rows: Sequence[Dict[str, Any]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = _clean(row.get(field))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return counts


def selection_counts(
    rows: Sequence[Dict[str, Any]],
    fields: Iterable[str],
    prefix: str,
    option_order: Sequence[str] | None = None,
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for field in fields:
        label = _label_from_field(field, prefix)
        count = sum(1 for row in rows if _clean(row.get(field)))
        counts[label] = count
    if option_order:
        return _ordered_counts(counts, option_order)
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def acceptance_stats(rows: Sequence[Dict[str, Any]], columns: Sequence[str], prefix: str) -> Dict[str, Dict[str, int]]:
    stats: Dict[str, Dict[str, int]] = {}
    for field in [col for col in columns if col.startswith(prefix)]:
        label = _label_from_field(field, prefix)
        values = value_counts(rows, field)
        stats[label] = {
            "允许": sum(count for value, count in values.items() if value.startswith("A.允许")),
            "允许但需要说明": sum(count for value, count in values.items() if value.startswith("B.允许但需要说明")),
            "不允许": sum(count for value, count in values.items() if value.startswith("C.不允许")),
        }
    return {label: stats.get(label, {"允许": 0, "允许但需要说明": 0, "不允许": 0}) for label in ACCEPTANCE_USE_OPTIONS}


def build_insights(result: Dict[str, Any]) -> List[str]:
    sample_size = result.get("sample_size", 0)
    daily = result.get("frequency_distribution", {}).get("A.每天都用", 0)
    training = result.get("training_gap_combined", {})
    ddl = result.get("ddl_pressure_combined", {})
    top_uses = [
        key for key, _ in sorted(
            result.get("ai_use_counts", {}).items(),
            key=lambda item: item[1],
            reverse=True,
        )[:3]
    ]

    insights = [
        "AI 已经成为大学生日常学习工具，需要把使用边界转化为更清晰的操作规范。",
        "学生普遍接受 AI 用于查资料、解释概念、列提纲、翻译和润色等非核心辅助。",
        "生成作业 / 论文核心内容在作业、论文和考试场景中均存在明显争议。",
        "工具强弱差异可能影响学习和作业表现，因此系统将其纳入偏见与公平风险。",
        "时间压力和课堂训练不足可能推动学生高风险使用 AI。系统需要提供及时的风险提醒和声明模板。",
    ]
    if sample_size:
        insights.insert(0, f"本次调研有效样本为 {sample_size} 份，其中每天使用 AI 的学生为 {daily} 人。")
    if top_uses:
        insights.append("调研中的 AI 用途前三项为：" + "、".join(top_uses) + "。")
    if training.get("count"):
        insights.append(
            f"经常或偶尔遇到作业超出课堂训练的学生为 {training['count']} 人，占 {training['rate']:.1f}%。"
        )
    if ddl.get("count"):
        insights.append(
            f"经常或偶尔因 DDL 临近而用 AI 救火的学生为 {ddl['count']} 人，占 {ddl['rate']:.1f}%。"
        )
    return insights


def _read_csv_text(text: str) -> Any:
    if pd is not None:
        frame = pd.read_csv(io.StringIO(text))
        frame = frame.dropna(how="all").fillna("")
        return frame

    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        cleaned = {key: _clean(value) for key, value in row.items() if key is not None}
        if any(cleaned.values()):
            rows.append(cleaned)
    return SimpleDataFrame(rows=rows, columns=reader.fieldnames or [])


def _records_and_columns(df: Any) -> tuple[List[Dict[str, Any]], List[str]]:
    if hasattr(df, "to_dict"):
        rows = df.to_dict("records")
    else:
        rows = list(getattr(df, "rows", []))
    columns = list(getattr(df, "columns", []))
    cleaned_rows = []
    for row in rows:
        cleaned = {key: _clean(value) for key, value in row.items()}
        if any(cleaned.values()):
            cleaned_rows.append(cleaned)
    return cleaned_rows, columns


def _rates(counts: Dict[str, int], sample_size: int) -> Dict[str, float]:
    if not sample_size:
        return {key: 0.0 for key in counts}
    return {key: round(value / sample_size * 100, 1) for key, value in counts.items()}


def _combined_count(counts: Dict[str, int], keys: Iterable[str], sample_size: int) -> Dict[str, float]:
    count = sum(counts.get(key, 0) for key in keys)
    rate = round(count / sample_size * 100, 1) if sample_size else 0.0
    return {"count": count, "rate": rate}


def _ordered_counts(counts: Dict[str, int], order: Sequence[str]) -> Dict[str, int]:
    ordered = {label: counts.get(label, 0) for label in order}
    ordered.update({label: count for label, count in counts.items() if label not in ordered})
    return ordered


def _label_from_field(field: str, prefix: str) -> str:
    return field.replace(prefix, "", 1).strip()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if text == "nan":
        return ""
    return text.strip()

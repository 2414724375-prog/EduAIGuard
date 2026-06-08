"""Utility helpers for EduAI-Guard."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FEEDBACK_PATH = DATA_DIR / "feedback.csv"
DEFAULT_SURVEY_PATH = DATA_DIR / "metadata_sample.csv"


def ensure_project_dirs() -> None:
    for name in ["data", "docs", "screenshots"]:
        (BASE_DIR / name).mkdir(exist_ok=True)


def append_feedback(feedback: Dict[str, str], path: Path = FEEDBACK_PATH) -> None:
    """Append one feedback row to CSV using UTF-8 BOM for spreadsheet compatibility."""

    ensure_project_dirs()
    fieldnames = ["提交时间", "是否有帮助", "最有用功能", "是否愿意声明AI使用", "开放建议"]
    row = {
        "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "是否有帮助": feedback.get("helpfulness", ""),
        "最有用功能": feedback.get("useful_feature", ""),
        "是否愿意声明AI使用": feedback.get("willingness", ""),
        "开放建议": feedback.get("comment", ""),
    }
    file_exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def read_feedback_records(path: Path = FEEDBACK_PATH) -> List[Dict[str, str]]:
    """Read feedback rows from CSV, returning an empty list when no data exists."""

    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            cleaned = {key: (value or "").strip() for key, value in row.items() if key}
            if any(cleaned.values()):
                rows.append(cleaned)
        return rows


def summarize_feedback(records: List[Dict[str, str]]) -> Dict[str, object]:
    """Summarize feedback rows for the local admin view."""

    return {
        "total": len(records),
        "helpfulness": _count_field(records, "是否有帮助"),
        "useful_feature": _count_field(records, "最有用功能"),
        "willingness": _count_field(records, "是否愿意声明AI使用"),
    }


def _count_field(records: List[Dict[str, str]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for record in records:
        value = record.get(field, "").strip()
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts


def risk_badge(level: str) -> str:
    mapping = {
        "低风险": "低风险",
        "中风险": "中风险",
        "高风险": "高风险",
        "严重风险": "严重风险",
    }
    return mapping.get(level, level)

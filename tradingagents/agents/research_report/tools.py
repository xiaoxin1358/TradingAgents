"""Tools for reading crawled research report txt files."""

import os
from pathlib import Path


def _read_folder(directory: str) -> str:
    """Read all .txt files in *directory*, concatenated with filename headers."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return f"[ERROR] Directory not found: {directory}"

    txt_files = sorted(dir_path.glob("*.txt"))
    if not txt_files:
        return f"[INFO] No .txt files found in: {directory}"

    parts: list[str] = []
    read_count = 0
    for fp in txt_files:
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception:
            parts.append(f"### File: {fp.name}\n[READ_ERROR] Cannot decode file.\n")
            continue
        if not content.strip():
            continue
        parts.append(f"### File: {fp.name}\n{content}\n")
        read_count += 1

    if not parts:
        return f"[INFO] All .txt files in {directory} were empty."

    header = f"[{read_count} file(s) read from {directory}]\n\n"
    return header + "\n".join(parts)


# Keep the old name for backward compatibility.
read_report_folder = _read_folder


def load_all_reports(report_root: str, analysis_date: str) -> dict[str, str]:
    """Read all 5 category folders and return raw texts keyed by state field name.

    Returns a dict suitable for merging into ResearchReportState:
        {"macro_raw": ..., "industry_raw": ..., ...}
    """
    categories = {
        "macro_raw": "宏观研究",
        "industry_raw": "行业研报",
        "stock_raw": "个股研报",
        "strategy_raw": "策略报告",
        "morning_raw": "券商晨报",
    }
    result = {}
    for field, folder in categories.items():
        path = os.path.join(report_root, analysis_date, folder)
        result[field] = _read_folder(path)
    return result

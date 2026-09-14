"""State for the research report reading agent system.

Independent from the main trading ``AgentState`` to keep concerns separated.
"""

from typing import Annotated

from langgraph.graph import MessagesState


class ResearchReportState(MessagesState):
    """Research report reading agent system state."""

    # ── Configuration ──
    report_root: Annotated[
        str, "Root directory of crawled report data, e.g. D:/WORKS/all_data/data/report_data"
    ]
    analysis_date: Annotated[
        str, "Analysis date (YYYY-MM-DD), used to resolve subfolders"
    ]

    # ── Raw report data (written by Data Loader, read by Readers) ──
    macro_raw: Annotated[str, "Raw macro report texts"]
    industry_raw: Annotated[str, "Raw industry report texts"]
    stock_raw: Annotated[str, "Raw stock report texts"]
    strategy_raw: Annotated[str, "Raw strategy report texts"]
    morning_raw: Annotated[str, "Raw morning brief texts"]

    # ── Category summaries (5 Readers) ──
    macro_summary: Annotated[str, "Macro Reader summary"]
    industry_summary: Annotated[str, "Industry Reader summary"]
    stock_summary: Annotated[str, "Stock Reader summary"]
    strategy_summary: Annotated[str, "Strategy Reader summary"]
    morning_summary: Annotated[str, "Morning Reader summary"]

    # ── Final output ──
    final_summary: Annotated[str, "Summary Manager: cross-validated investment advice"]

    # ── Contradiction analysis (v3.0) ──
    claims: Annotated[str, "当日全部 Claim 元组（JSON 字符串）"]
    contradictions: Annotated[str, "当日判定结果（JSON 字符串）"]
    contradiction_report: Annotated[str, "矛盾分析报告（markdown）"]
    contradiction_insights: Annotated[str, "矛盾洞察（FR-7，JSON 字符串）"]

    # ── Metadata ──
    files_read: Annotated[
        int, "Number of files read this run"
    ]

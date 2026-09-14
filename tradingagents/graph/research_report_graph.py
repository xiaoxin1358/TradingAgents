"""Research Report Graph — Data Loader → 5 parallel Readers → Summary Manager + contradiction branch.

v2.0: A unified Data Loader pre-fetches all 5 category folders into state
fields (*_raw).  Five pure-LLM Reader nodes then analyse their respective
raw data in parallel (no tools, no message pollution).  Finally, the Summary
Manager cross-validates all summaries and produces the final recommendation.

v3.0: A contradiction branch runs AFTER the Summary Manager (serial):
Claim Extractor (quick) → Contradiction Judge (deep) → Contradiction Report.
The Claim Extractor additionally reads the produced final_summary as an
enhanced input, and each branch node is fault-tolerant so a failure in the
contradiction branch never blocks the main chain's report.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from tradingagents.agents.research_report.claim_extractor import create_claim_extractor
from tradingagents.agents.research_report.contradiction_judge import create_contradiction_judge
from tradingagents.agents.research_report.contradiction_report import (
    create_contradiction_insight,
    create_contradiction_report,
)
from tradingagents.agents.research_report.contradiction_store import ContradictionStore
from tradingagents.agents.research_report.industry_reader import create_industry_reader
from tradingagents.agents.research_report.macro_reader import create_macro_reader
from tradingagents.agents.research_report.morning_reader import create_morning_reader
from tradingagents.agents.research_report.state import ResearchReportState
from tradingagents.agents.research_report.stock_reader import create_stock_reader
from tradingagents.agents.research_report.strategy_reader import create_strategy_reader
from tradingagents.agents.research_report.summary_manager import (
    create_summary_manager,
    create_summary_msg_delete,
)
from tradingagents.agents.research_report.tools import load_all_reports

logger = logging.getLogger(__name__)

# Reader definitions: (node_key, factory, state_raw_field)
_READERS = [
    ("Macro Reader", create_macro_reader),
    ("Industry Reader", create_industry_reader),
    ("Stock Reader", create_stock_reader),
    ("Strategy Reader", create_strategy_reader),
    ("Morning Reader", create_morning_reader),
]


def _data_loader_node(state: dict) -> dict:
    """Pre-load all 5 category folders into state *_raw fields (no LLM)."""
    return load_all_reports(state["report_root"], state["analysis_date"])


class ResearchReportGraph:
    """v3.0: Data Loader → 5 parallel Readers → Summary Manager → contradiction branch (serial)."""

    def __init__(self, quick_llm: Any, deep_llm: Any, db_path: str = "reports/contradictions.db"):
        self.quick_llm = quick_llm
        self.deep_llm = deep_llm
        self.contradiction_store = ContradictionStore(db_path)
        self._graph = self._build()

    def _build(self):
        workflow = StateGraph(ResearchReportState)

        # ── Data Loader (I/O only, no LLM) ──
        workflow.add_node("Data Loader", _data_loader_node)

        # ── 5 parallel Readers (pure LLM, no tools) ──
        for node_key, factory in _READERS:
            workflow.add_node(node_key, factory(self.quick_llm))

        # ── Summary Manager (deep LLM, cross-validation) ──
        workflow.add_node("Summary Manager", create_summary_manager(self.deep_llm))
        workflow.add_node("Msg Clear Summary", create_summary_msg_delete())

        # ── Contradiction analysis branch (v3.1: Judge → Insight → Report) ──
        workflow.add_node("Claim Extractor", create_claim_extractor(self.quick_llm))
        workflow.add_node(
            "Contradiction Judge",
            create_contradiction_judge(self.deep_llm, self.contradiction_store),
        )
        workflow.add_node(
            "Contradiction Insight",
            create_contradiction_insight(self.deep_llm, self.contradiction_store),
        )
        workflow.add_node(
            "Contradiction Report",
            create_contradiction_report(self.contradiction_store),
        )

        # ── Edges ──
        workflow.add_edge(START, "Data Loader")

        # Fan-out: Data Loader → all 5 Readers (parallel)
        for node_key, _factory in _READERS:
            workflow.add_edge("Data Loader", node_key)

        # Fan-in: all 5 Readers → Summary Manager
        for node_key, _factory in _READERS:
            workflow.add_edge(node_key, "Summary Manager")

        # 串行：研报分析完成后 → 冲突分析（Claim Extractor 额外读取 final_summary 作为增强输入）
        workflow.add_edge("Summary Manager", "Claim Extractor")
        workflow.add_edge("Claim Extractor", "Contradiction Judge")
        workflow.add_edge("Contradiction Judge", "Contradiction Insight")
        workflow.add_edge("Contradiction Insight", "Contradiction Report")
        workflow.add_edge("Contradiction Report", END)

        workflow.add_edge("Summary Manager", "Msg Clear Summary")
        workflow.add_edge("Msg Clear Summary", END)

        return workflow.compile()

    def run(self, report_root: str, analysis_date: str) -> dict:
        """Run the graph and return the final state dict."""
        initial_state = {
            "report_root": report_root,
            "analysis_date": analysis_date,
            "messages": [],
        }
        logger.info("Starting research report analysis: root=%s, date=%s", report_root, analysis_date)
        result = self._graph.invoke(initial_state)
        logger.info("Research report analysis complete.")
        return result

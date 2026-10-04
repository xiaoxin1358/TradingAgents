"""End-to-end test for the v3.0 research report graph + contradiction branch.

Uses FakeLLMs (no network) so the full graph — Data Loader → 5 Readers →
Summary Manager → Claim Extractor → Judge → Report (serial) — runs
deterministically against a temp report root and a temp SQLite db.

M1 self-checks from docs/research-report-contradiction.md:
  * contradiction_report.md content is produced into state
  * the contradictions table gets records
  * running twice reuses the same id (no duplicate rows)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage

from tradingagents.agents.research_report.contradiction_store import contradiction_id
from tradingagents.graph.research_report_graph import ResearchReportGraph

CATEGORIES = ["宏观研究", "行业研报", "个股研报", "策略报告", "券商晨报"]

# Canned JSON payloads
_CLAIMS = [
    {"broker": "国元", "author": None, "report_type": "策略",
     "subject": "AI算力", "direction": -1, "strength": 0.6,
     "horizon": "中期", "target": None, "quote": "阶段性减配热门科技"},
    {"broker": "中邮", "author": None, "report_type": "个股",
     "subject": "AI算力", "direction": 1, "strength": 0.7,
     "horizon": "中期", "target": None, "quote": "买入评级"},
]

# 矛盾信号专用抽取（第二次调用）返回的成对 claim：光模块 基本面 vs 隔夜美股暴跌
_CONFLICT_CLAIMS = [
    {"broker": "东吴", "author": None, "report_type": "综合",
     "subject": "光模块", "direction": 1, "strength": 0.7,
     "horizon": "中期", "target": None, "quote": "基本面高景气，FCC禁令落地难度大"},
    {"broker": "SummaryManager", "author": None, "report_type": "综合",
     "subject": "光模块", "direction": -1, "strength": 0.5,
     "horizon": "短期", "target": None, "quote": "隔夜美股光通信板块暴跌，情绪传导风险"},
]

_JUDGE = [
    {"subject": "AI算力", "kind": "opinion", "scope": "direct", "scale": "same",
     "claim_a": _CLAIMS[0], "claim_b": _CLAIMS[1],
     "horizon_a": "中期", "horizon_b": "中期"},
    {"subject": "光模块", "kind": "opinion", "scope": "direct", "scale": "cross",
     "claim_a": _CONFLICT_CLAIMS[0], "claim_b": _CONFLICT_CLAIMS[1],
     "horizon_a": "中期", "horizon_b": "短期"},
]

_INSIGHT_ID = contradiction_id(_CLAIMS[0], _CLAIMS[1], "AI算力", "opinion")
_INSIGHTS = [
    {"id": _INSIGHT_ID, "cause_type": "框架假设", "cause": "双方关键假设不同",
     "analysis": "国元看拥挤度，中邮看需求", "watch": "跟踪云厂商资本开支",
     "tilt": "不确定"},
]


class FakeLLM:
    """Routes by the first SystemMessage keyword to a canned response.

    Supports both ``llm.invoke([...])`` (Readers, Claim Extractor, Judge) and
    ``prompt | llm`` (Summary Manager, which passes a ChatPromptValue).
    """

    def __init__(self, routes: dict[str, str]):
        self.routes = routes
        self.calls = 0
        self.last_human = ""

    def _respond(self, messages):
        self.calls += 1
        if hasattr(messages, "to_messages"):  # ChatPromptValue from prompt | llm
            messages = messages.to_messages()
        elif isinstance(messages, dict):
            messages = messages.get("messages", [])
        system = ""
        for m in messages:
            if getattr(m, "type", "") == "system":
                system = m.content
            elif getattr(m, "type", "") == "human":
                self.last_human = m.content
        for kw, resp in self.routes.items():
            if kw in system:
                return AIMessage(content=resp)
        return AIMessage(content="（默认摘要）")

    def invoke(self, messages):
        return self._respond(messages)

    def __call__(self, messages):
        return self._respond(messages)


def _make_report_root(tmp_path: Path) -> Path:
    """Create {root}/{date}/{分类}/*.txt so the Data Loader has something to read."""
    root = tmp_path / "report_root"
    day = "2026-08-10"
    for cat in CATEGORIES:
        folder = root / day / cat
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "a.txt").write_text(
            f"### File: a.txt\n标题: 测试研报\n正文: {cat}相关观点。", encoding="utf-8"
        )
    return root


def _make_llms():
    quick = FakeLLM(
        {
            "观点抽取器": json.dumps(_CLAIMS, ensure_ascii=False),
            "矛盾信号解析器": json.dumps(_CONFLICT_CLAIMS, ensure_ascii=False),
            "Stock Research Analyst": "## 个股研报总结\n测试",
            "Macro": "## 宏观研究总结\n测试",
            "Industry": "## 行业研报总结\n测试",
            "Strategy": "## 策略报告总结\n测试",
            "Morning": "## 券商晨报总结\n测试",
        }
    )
    deep = FakeLLM(
        {
            "矛盾判定器": json.dumps(_JUDGE, ensure_ascii=False),
            "矛盾分析专家": json.dumps(_INSIGHTS, ensure_ascii=False),
            "Chief Investment Strategist": "## 投资建议综合报告\n测试",
        }
    )
    return quick, deep


@pytest.fixture()
def run_graph(tmp_path):
    """Factory that runs the graph once and returns (state, db_path, quick, deep)."""

    def _run():
        root = _make_report_root(tmp_path)
        db_path = str(tmp_path / "contradictions.db")
        quick, deep = _make_llms()
        graph = ResearchReportGraph(quick_llm=quick, deep_llm=deep, db_path=db_path)
        state = graph.run(report_root=str(root), analysis_date="2026-08-10")
        return state, db_path, quick, deep

    return _run


@pytest.mark.integration
def test_graph_produces_both_reports(run_graph):
    state, db_path, quick, deep = run_graph()

    # 主链路不受影响
    assert "最终投資建議" not in state.get("final_summary", "")
    assert state.get("final_summary")  # non-empty

    # 矛盾分支产出报告
    report = state.get("contradiction_report", "")
    assert "矛盾信号分析报告" in report
    assert "AI算力" in report
    assert "📊 矛盾统计" in report

    # 串行增强：Claim Extractor 的第二次调用（矛盾信号专用抽取）读到了 final_summary
    assert "矛盾信号段落" in quick.last_human

    # 矛盾信号配对（光模块）经 Judge 检出并渲染
    assert "光模块" in report

    # FR-7：洞察已生成并渲染到报告
    assert "📝 **洞察**" in report
    assert "框架假设" in report

    # DB 落库
    import sqlite3

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, status FROM contradictions").fetchall()
    conn.close()
    assert len(rows) == 2  # AI算力 + 光模块（矛盾信号配对）
    assert all(status == "open" for _, status in rows)


@pytest.mark.integration
def test_rerun_reuses_id_no_duplicate(run_graph):
    state1, db_path, quick1, deep1 = run_graph()
    state2, _, quick2, deep2 = run_graph()

    import sqlite3

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, first_seen, last_seen FROM contradictions"
    ).fetchall()
    conn.close()

    # 同一个 id 只保留一行（first_seen 保留，last_seen 刷新）
    assert len(rows) == 2  # AI算力 + 光模块，各一行，无重复
    ids = {cid for cid, _, _ in rows}
    assert any("AI算力" in cid for cid in ids)
    assert any("光模块" in cid for cid in ids)
    for _cid, first_seen, last_seen in rows:
        assert first_seen == "2026-08-10"
        assert last_seen == "2026-08-10"

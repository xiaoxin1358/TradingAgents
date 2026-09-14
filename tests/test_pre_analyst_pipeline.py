"""Integration tests for the pre_analyst linear pipeline.

Uses a mock LLM so no API key is required — we only verify that the pipeline
wires up and the nodes execute in the correct linear order.
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from tradingagents.agents.pre_analyst import (
    create_cyclical_analyst,
    create_defensive_analyst,
    create_growth_analyst,
    create_sector_manager,
)
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import create_msg_delete


def _make_mock_llm(responses: list):
    """Callable mock LLM returning real AIMessages, counting invocations."""
    mock_llm = MagicMock()

    def _invoke(messages):
        if not responses:
            raise RuntimeError("No more mock responses")
        return AIMessage(content=responses.pop(0))

    mock_llm.bind_tools.return_value = MagicMock(side_effect=_invoke)
    return mock_llm


def _make_router(tool_node: str, clear_node: str):
    """Route tool_calls → tool node, otherwise → message-clear node."""

    def _route(state: AgentState) -> str:
        last = state["messages"][-1]
        return tool_node if last.tool_calls else clear_node

    return _route


def _build_test_graph(mock_llm: MagicMock):
    """Build the linear pipeline graph (mirrors GraphSetup's fixed edges)."""
    workflow = StateGraph(AgentState)

    workflow.add_node("Cyclical Analyst", create_cyclical_analyst(mock_llm))
    workflow.add_node("Growth Analyst", create_growth_analyst(mock_llm))
    workflow.add_node("Defensive Analyst", create_defensive_analyst(mock_llm))
    workflow.add_node("Sector Manager", create_sector_manager(mock_llm))

    pipeline = (
        ("Cyclical Analyst", "Msg Clear Cyclical", "tools_cyclical", "Growth Analyst"),
        ("Growth Analyst", "Msg Clear Growth", "tools_growth", "Defensive Analyst"),
        ("Defensive Analyst", "Msg Clear Defensive", "tools_defensive", "Sector Manager"),
        ("Sector Manager", "Msg Clear Sector", "tools_sector_manager", END),
    )
    for _analyst, clear, tool, _next in pipeline:
        workflow.add_node(tool, MagicMock(return_value={}))
        workflow.add_node(clear, create_msg_delete())

    workflow.add_edge(START, "Cyclical Analyst")

    for analyst, clear, tool, next_node in pipeline:
        workflow.add_conditional_edges(
            analyst,
            _make_router(tool, clear),
            [tool, clear],
        )
        workflow.add_edge(clear, next_node)

    return workflow.compile()


@pytest.mark.integration
class TestPreAnalystPipeline:
    """Verify the linear pre-analyst pipeline runs end-to-end with mock LLM."""

    def test_graph_compiles_and_runs_linear_chain(self):
        mock_llm = _make_mock_llm([
            "Cyclical view: energy and financials.",
            "Growth view: AI and biotech.",
            "Defensive view: staples and healthcare.",
            "## Sector Recommendation\n\n### Preferred Sectors\n...",
        ])

        graph = _build_test_graph(mock_llm)

        final_state = graph.invoke({
            "messages": [("human", "Which sectors?")],
            "trade_date": "2026-07-07",
            "company_of_interest": "SPY",
            "instrument_context": "Testing the pre-analyst pipeline.",
            "cyclical_report": "",
            "growth_report": "",
            "defensive_report": "",
            "sector_recommendation": "",
        }, {"recursion_limit": 50})

        assert "energy and financials" in final_state["cyclical_report"]
        assert "AI and biotech" in final_state["growth_report"]
        assert "staples and healthcare" in final_state["defensive_report"]
        assert "Sector Recommendation" in final_state["sector_recommendation"]

    def test_pipeline_order_is_preserved(self):
        """Verify LLM is invoked 4 times in the correct order."""
        mock_llm = _make_mock_llm([
            "Cyclical output.",
            "Growth output.",
            "Defensive output.",
            "Manager output.",
        ])

        graph = _build_test_graph(mock_llm)
        graph.invoke({
            "messages": [("human", "Test")],
            "trade_date": "2026-07-07",
            "company_of_interest": "SPY",
            "instrument_context": "Testing the pre-analyst pipeline.",
            "cyclical_report": "",
            "growth_report": "",
            "defensive_report": "",
            "sector_recommendation": "",
        }, {"recursion_limit": 50})

        assert mock_llm.bind_tools.return_value.call_count == 4


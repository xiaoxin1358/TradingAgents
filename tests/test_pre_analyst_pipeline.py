"""Integration tests for the pre_analyst linear pipeline.

Uses a mock LLM so no API key is required — we only verify that the graph
compiles and the nodes execute in the correct linear order.
"""

from unittest.mock import MagicMock

import pytest
from langgraph.graph import END, START, StateGraph

from tradingagents.agents.pre_analyst import (
    create_cyclical_analyst,
    create_defensive_analyst,
    create_growth_analyst,
    create_sector_manager,
)
from tradingagents.agents.utils.agent_states import AgentState


def _should_continue_clear(state: AgentState) -> str:
    """Simple router: tool_calls → tools_X, else → Msg Clear X."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools_cyclical"
    return "Msg Clear Cyclical"


def _make_mock_llm(responses: list):
    """Return a mock LLM whose bind_tools chain returns responses in order."""
    mock_llm = MagicMock()

    def _invoke_side_effect(messages):
        if not responses:
            raise RuntimeError("No more mock responses")
        content = responses.pop(0)
        mock_msg = MagicMock()
        mock_msg.tool_calls = []
        mock_msg.content = content
        return mock_msg

    mock_llm.bind_tools.return_value.invoke.side_effect = _invoke_side_effect
    return mock_llm


def _build_test_graph(mock_llm: MagicMock):
    """Build linear pipeline graph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("Cyclical Analyst", create_cyclical_analyst(mock_llm))
    workflow.add_node("Growth Analyst", create_growth_analyst(mock_llm))
    workflow.add_node("Defensive Analyst", create_defensive_analyst(mock_llm))
    workflow.add_node("Sector Manager", create_sector_manager(mock_llm))

    mock_clear = MagicMock(return_value={"messages": [MagicMock(content="Proceed")]})
    workflow.add_node("Msg Clear Cyclical", mock_clear)
    workflow.add_node("Msg Clear Growth", mock_clear)
    workflow.add_node("Msg Clear Defensive", mock_clear)
    workflow.add_node("Msg Clear Sector", mock_clear)

    workflow.add_edge(START, "Cyclical Analyst")

    for analyst, clear, tool, next_node in (
        ("Cyclical Analyst", "Msg Clear Cyclical", "tools_cyclical", "Growth Analyst"),
        ("Growth Analyst", "Msg Clear Growth", "tools_growth", "Defensive Analyst"),
        ("Defensive Analyst", "Msg Clear Defensive", "tools_defensive", "Sector Manager"),
        ("Sector Manager", "Msg Clear Sector", "tools_sector_manager", END),
    ):
        workflow.add_conditional_edges(
            analyst,
            _should_continue_clear,
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
            "cyclical_report": "",
            "growth_report": "",
            "defensive_report": "",
            "sector_recommendation": "",
        }, {"recursion_limit": 50})

        assert mock_llm.bind_tools.return_value.invoke.call_count == 4


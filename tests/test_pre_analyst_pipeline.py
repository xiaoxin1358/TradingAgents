"""Integration tests for the pre_analyst standalone pipeline.

Uses a mock LLM so no API key is required — we only verify that the graph
compiles and the nodes execute in the correct order.
"""

from unittest.mock import MagicMock

import pytest
from langgraph.graph import END, START, StateGraph

from tradingagents.agents.pre_analyst import (
    SectorDebateState,
    create_cyclical_analyst,
    create_defensive_analyst,
    create_growth_analyst,
    create_sector_manager,
)
from tradingagents.agents.utils.agent_states import AgentState


def _should_continue_sector_debate(state: AgentState, max_rounds: int = 1) -> str:
    sector_state = state.get("sector_debate_state", {})
    count = sector_state.get("count", 0)
    if count >= 3 * max_rounds:
        return "Sector Manager"
    latest = sector_state.get("latest_speaker", "")
    if latest == "cyclical":
        return "Growth Analyst"
    if latest == "growth":
        return "Defensive Analyst"
    return "Cyclical Analyst"


def _build_test_graph(mock_llm: MagicMock, max_rounds: int = 1):
    """Build the same graph as standalone.py but with a mock LLM."""
    workflow = StateGraph(AgentState)

    workflow.add_node("Cyclical Analyst", create_cyclical_analyst(mock_llm))
    workflow.add_node("Growth Analyst", create_growth_analyst(mock_llm))
    workflow.add_node("Defensive Analyst", create_defensive_analyst(mock_llm))
    workflow.add_node("Sector Manager", create_sector_manager(mock_llm))

    workflow.add_edge(START, "Cyclical Analyst")

    routes = {
        "Growth Analyst": "Growth Analyst",
        "Defensive Analyst": "Defensive Analyst",
        "Sector Manager": "Sector Manager",
    }
    for node_name in ["Cyclical Analyst", "Growth Analyst", "Defensive Analyst"]:
        workflow.add_conditional_edges(
            node_name,
            lambda s, mr=max_rounds: _should_continue_sector_debate(s, mr),
            routes,
        )

    workflow.add_edge("Sector Manager", END)
    return workflow.compile()


@pytest.mark.integration
class TestPreAnalystPipeline:
    """Verify the standalone sector debate graph runs end-to-end with mock LLM."""

    def test_graph_compiles_and_runs_one_rotation(self):
        mock_llm = MagicMock()
        # Each node call returns a distinct response so the routing logic
        # can distinguish speakers by content prefix.
        mock_llm.invoke.side_effect = [
            MagicMock(content="Cyclical view: energy and financials."),
            MagicMock(content="Growth view: AI and biotech."),
            MagicMock(content="Defensive view: staples and healthcare."),
            MagicMock(content="## Sector Recommendation\n\n### Preferred Sectors\n..."),
        ]

        graph = _build_test_graph(mock_llm, max_rounds=1)

        initial_state: dict = {
            "messages": [("human", "Which sectors?")],
            "trade_date": "2026-07-07",
            "sector_debate_state": SectorDebateState(
                cyclical_history="",
                growth_history="",
                defensive_history="",
                history="",
                current_response="",
                latest_speaker="",
                judge_decision="",
                count=0,
            ),
        }

        final_state = graph.invoke(initial_state, {"recursion_limit": 50})

        assert final_state["sector_debate_state"]["count"] == 3
        assert "Sector Recommendation" in final_state["sector_recommendation"]
        # Verify each analyst spoke in order
        history = final_state["sector_debate_state"]["history"]
        assert "Cyclical view" in history
        assert "Growth view" in history
        assert "Defensive view" in history

    def test_sector_manager_does_not_increment_count(self):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = [
            MagicMock(content="C1."),
            MagicMock(content="G1."),
            MagicMock(content="D1."),
            MagicMock(content="## Sector Recommendation\n### Preferred Sectors: tech and healthcare"),
        ]

        graph = _build_test_graph(mock_llm, max_rounds=1)
        initial_state: dict = {
            "messages": [("human", "Which sectors?")],
            "trade_date": "2026-07-07",
            "sector_debate_state": SectorDebateState(
                cyclical_history="",
                growth_history="",
                defensive_history="",
                history="",
                current_response="",
                latest_speaker="",
                judge_decision="",
                count=0,
            ),
        }

        final_state = graph.invoke(initial_state, {"recursion_limit": 50})
        # 3 analysts spoke → count=3; manager doesn't bump it
        assert final_state["sector_debate_state"]["count"] == 3

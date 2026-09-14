"""Unit tests for pre-analyst AgentState report fields."""

import pytest

from tradingagents.agents.utils.agent_states import AgentState


@pytest.mark.unit
class TestPreAnalystState:
    """Verify pre-analyst report fields in AgentState."""

    def test_default_report_fields_are_empty(self):
        state = AgentState(
            messages=[("human", "Test")],
            cyclical_report="",
            growth_report="",
            defensive_report="",
            sector_recommendation="",
        )
        assert state["cyclical_report"] == ""
        assert state["growth_report"] == ""
        assert state["defensive_report"] == ""
        assert state["sector_recommendation"] == ""

    def test_reports_accept_string_content(self):
        state = AgentState(
            messages=[("human", "Test")],
            cyclical_report="Energy sector analysis.",
            growth_report="Tech sector analysis.",
            defensive_report="Staples sector analysis.",
            sector_recommendation="Overweight tech.",
        )
        assert "Energy" in state["cyclical_report"]
        assert "Tech" in state["growth_report"]
        assert "Staples" in state["defensive_report"]
        assert "Overweight" in state["sector_recommendation"]


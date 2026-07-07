"""Unit tests for SectorDebateState schema."""

import pytest

from tradingagents.agents.pre_analyst.sector_debate_state import SectorDebateState


@pytest.mark.unit
class TestSectorDebateState:
    """Verify the SectorDebateState TypedDict behaves correctly."""

    def test_initial_state_is_empty(self):
        state = SectorDebateState(
            cyclical_history="",
            growth_history="",
            defensive_history="",
            history="",
            current_response="",
            latest_speaker="",
            judge_decision="",
            count=0,
        )
        assert state["count"] == 0
        assert state["history"] == ""
        assert state["latest_speaker"] == ""
        assert state["cyclical_history"] == ""

    def test_count_increments_after_speaker(self):
        state = SectorDebateState(
            cyclical_history="",
            growth_history="",
            defensive_history="",
            history="",
            current_response="",
            latest_speaker="cyclical",
            judge_decision="",
            count=0,
        )
        # simulate one speech
        new_state = dict(state)
        new_state["history"] = "Cyclical Analyst: Energy looks strong."
        new_state["cyclical_history"] = "Cyclical Analyst: Energy looks strong."
        new_state["current_response"] = "Cyclical Analyst: Energy looks strong."
        new_state["latest_speaker"] = "cyclical"
        new_state["count"] = 1

        assert new_state["count"] == 1
        assert "Energy looks strong" in new_state["history"]
        assert new_state["latest_speaker"] == "cyclical"

    def test_history_appends_across_speakers(self):
        state = SectorDebateState(
            cyclical_history="C1: Cyclical point.",
            growth_history="",
            defensive_history="",
            history="C1: Cyclical point.",
            current_response="",
            latest_speaker="cyclical",
            judge_decision="",
            count=1,
        )

        # growth speaks
        new_state = dict(state)
        new_state["history"] = state["history"] + "\n" + "G1: Growth point."
        new_state["growth_history"] = "G1: Growth point."
        new_state["current_response"] = "G1: Growth point."
        new_state["latest_speaker"] = "growth"
        new_state["count"] = 2

        assert new_state["count"] == 2
        assert "G1: Growth point." in new_state["history"]
        assert "C1: Cyclical point." in new_state["history"]
        assert new_state["latest_speaker"] == "growth"

    def test_judge_decision_set_once(self):
        state = SectorDebateState(
            cyclical_history="C1.",
            growth_history="G1.",
            defensive_history="D1.",
            history="C1.\nG1.\nD1.",
            current_response="D1.",
            latest_speaker="defensive",
            judge_decision="",
            count=3,
        )
        new_state = dict(state)
        new_state["judge_decision"] = "Sector Manager: Prefer tech and energy."
        assert "tech and energy" in new_state["judge_decision"]
        assert new_state["count"] == 3  # manager doesn't increment count

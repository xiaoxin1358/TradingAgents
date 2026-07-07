"""Unit tests for pre_analyst agent node functions (mock LLM)."""

from unittest.mock import MagicMock

import pytest

from tradingagents.agents.pre_analyst import (
    create_cyclical_analyst,
    create_defensive_analyst,
    create_growth_analyst,
    create_sector_manager,
)


@pytest.mark.unit
class TestCyclicalAnalyst:
    def test_returns_sector_debate_state_with_correct_keys(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Cyclical: Energy and financials are poised to outperform.")

        node = create_cyclical_analyst(mock_llm)
        result = node({"sector_debate_state": _empty_sector_state(), "trade_date": "2026-07-07"})

        assert "sector_debate_state" in result
        s = result["sector_debate_state"]
        assert s["count"] == 1
        assert s["latest_speaker"] == "cyclical"
        assert "Energy and financials" in s["current_response"]
        assert s["current_response"].startswith("Cyclical Analyst:")


@pytest.mark.unit
class TestGrowthAnalyst:
    def test_returns_sector_debate_state_with_correct_keys(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Growth: AI and clean energy are the future.")

        node = create_growth_analyst(mock_llm)
        result = node({"sector_debate_state": _empty_sector_state(), "trade_date": "2026-07-07"})

        s = result["sector_debate_state"]
        assert s["count"] == 1
        assert s["latest_speaker"] == "growth"
        assert s["current_response"].startswith("Growth Analyst:")


@pytest.mark.unit
class TestDefensiveAnalyst:
    def test_returns_sector_debate_state_with_correct_keys(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Defensive: Staples and utilities offer safety right now.")

        node = create_defensive_analyst(mock_llm)
        result = node({"sector_debate_state": _empty_sector_state(), "trade_date": "2026-07-07"})

        s = result["sector_debate_state"]
        assert s["count"] == 1
        assert s["latest_speaker"] == "defensive"
        assert s["current_response"].startswith("Defensive Analyst:")


@pytest.mark.unit
class TestSectorManager:
    def test_returns_recommendation_and_preserves_debate_state(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="## Sector Recommendation\n...")

        debate = _empty_sector_state()
        debate["history"] = "C1.\nG1.\nD1."
        debate["count"] = 3

        node = create_sector_manager(mock_llm)
        result = node({"sector_debate_state": debate, "trade_date": "2026-07-07"})

        assert "sector_debate_state" in result
        assert "sector_recommendation" in result
        assert result["sector_recommendation"] is not None
        assert result["sector_debate_state"]["judge_decision"] == result["sector_recommendation"]
        assert result["sector_debate_state"]["count"] == 3  # unchanged


# ── helpers ──

def _empty_sector_state() -> dict:
    return {
        "cyclical_history": "",
        "growth_history": "",
        "defensive_history": "",
        "history": "",
        "current_response": "",
        "latest_speaker": "",
        "judge_decision": "",
        "count": 0,
    }

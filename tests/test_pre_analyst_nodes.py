"""Unit tests for pre_analyst agent node functions (mock LLM, pipeline pattern).

The nodes build ``prompt | llm.bind_tools(tools)``, so the mock LLM must be
callable (``mock.return_value``) and must yield a real ``AIMessage`` — nodes
return it in ``{"messages": [...]}``, which LangGraph validates.
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from tradingagents.agents.pre_analyst import (
    create_cyclical_analyst,
    create_defensive_analyst,
    create_growth_analyst,
    create_sector_manager,
)

# ── helpers ──

def _base_state(**overrides) -> dict:
    s = {
        "messages": [("human", "Analyse sectors.")],
        "trade_date": "2026-07-07",
        "cyclical_report": "",
        "growth_report": "",
        "defensive_report": "",
        "sector_recommendation": "",
    }
    s.update(overrides)
    return s


def _mock_llm_returning(message: AIMessage) -> MagicMock:
    """Mock whose ``bind_tools(...)`` is callable and returns ``message``."""
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = MagicMock(return_value=message)
    return mock_llm


@pytest.mark.unit
class TestCyclicalAnalyst:
    def test_returns_cyclical_report_when_no_tool_calls(self):
        mock_llm = _mock_llm_returning(
            AIMessage(content="Cyclical: Energy and financials are poised to outperform.")
        )

        node = create_cyclical_analyst(mock_llm)
        result = node(_base_state())

        assert "cyclical_report" in result
        assert result["cyclical_report"] == "Cyclical: Energy and financials are poised to outperform."
        assert "messages" in result

    def test_returns_empty_report_when_tool_calls_present(self):
        mock_llm = _mock_llm_returning(
            AIMessage(content="", tool_calls=[
                {"name": "get_global_news", "args": {}, "id": "call_1"},
            ])
        )

        node = create_cyclical_analyst(mock_llm)
        result = node(_base_state())

        assert result["cyclical_report"] == ""
        assert "messages" in result


@pytest.mark.unit
class TestGrowthAnalyst:
    def test_returns_growth_report_when_no_tool_calls(self):
        mock_llm = _mock_llm_returning(
            AIMessage(content="Growth: AI and clean energy are the future.")
        )

        node = create_growth_analyst(mock_llm)
        result = node(_base_state())

        assert result["growth_report"] == "Growth: AI and clean energy are the future."
        assert "messages" in result


@pytest.mark.unit
class TestDefensiveAnalyst:
    def test_returns_defensive_report_when_no_tool_calls(self):
        mock_llm = _mock_llm_returning(
            AIMessage(content="Defensive: Staples and utilities offer safety.")
        )

        node = create_defensive_analyst(mock_llm)
        result = node(_base_state())

        assert result["defensive_report"] == "Defensive: Staples and utilities offer safety."
        assert "messages" in result


@pytest.mark.unit
class TestSectorManager:
    def test_returns_sector_recommendation(self):
        mock_llm = _mock_llm_returning(
            AIMessage(content="## Sector Recommendation\n\n### Preferred Sectors\n...")
        )

        node = create_sector_manager(mock_llm)
        result = node(_base_state(
            cyclical_report="C: Energy and financials.",
            growth_report="G: AI and biotech.",
            defensive_report="D: Staples and healthcare.",
        ))

        assert "sector_recommendation" in result
        assert "Sector Recommendation" in result["sector_recommendation"]
        assert "messages" in result

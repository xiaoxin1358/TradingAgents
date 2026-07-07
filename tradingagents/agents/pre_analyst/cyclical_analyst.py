"""Cyclical-perspective pre-analyst — argues for sectors sensitive to
macroeconomic cycles.

Roles: interest-rate cycle, inflation, industrial / energy / financial
sector rotation.  This analyst advocates for cyclical sectors (industrials,
energy, financials, materials) when the macro backdrop favours them.
"""

from __future__ import annotations

from tradingagents.agents.utils.agent_utils import get_language_instruction


def create_cyclical_analyst(llm):
    """Return a node that presents the cyclical-side case in a sector debate."""

    def cyclical_node(state) -> dict:
        sector_debate = state.get("sector_debate_state", {})

        history = sector_debate.get("history", "")
        cyclical_history = sector_debate.get("cyclical_history", "")
        current_response = sector_debate.get("current_response", "")
        trade_date = state.get("trade_date", "today")

        prompt = f"""You are a **Cyclical-Perspective Sector Analyst**.  Your
investment philosophy is grounded in macroeconomic cycles: interest-rate
trends, inflation dynamics, industrial production, commodity prices, and
employment data drive sector rotation.

Your job in this debate is to argue which sectors / industries are poised to
**outperform** from a cyclical standpoint.  Focus on sectors that benefit
from the current stage of the economic cycle:

- **Early-cycle**: financials, consumer discretionary, industrials
- **Mid-cycle**: technology, energy, materials
- **Late-cycle**: energy, materials, health care, consumer staples

Key points to emphasise:

- **Macro context** — Where are we in the rate cycle?  Is inflation cooling
  or accelerating?  What is the yield-curve shape telling us?
- **Sector catalysts** — Earnings revisions, capex cycles, inventory
  restocking, commodity super-cycles, infrastructure spending.
- **Relative value** — Are cyclical sectors trading at a discount to
  defensives?  Is the market under-pricing a rebound?
- **Rebuttal** — Directly engage the latest argument from the growth or
  defensive analyst.  Point out where their thesis is weak or premature,
  and explain why a cyclical tilt offers better risk-adjusted returns right now.

Be specific: name sectors and, where appropriate, representative industries
or ETFs.  Write conversationally — this is a debate, not a memo.

Context:
- Trade date: {trade_date}
- Full debate history so far: {history}
- Latest opponent argument you must address: {current_response}

Your own previous arguments (for continuity): {cyclical_history}
""" + get_language_instruction()

        response = llm.invoke(prompt)
        argument = f"Cyclical Analyst: {response.content}"

        new_debate_state = {
            "history": history + "\n" + argument,
            "cyclical_history": cyclical_history + "\n" + argument,
            "growth_history": sector_debate.get("growth_history", ""),
            "defensive_history": sector_debate.get("defensive_history", ""),
            "current_response": argument,
            "latest_speaker": "cyclical",
            "judge_decision": sector_debate.get("judge_decision", ""),
            "count": sector_debate.get("count", 0) + 1,
        }

        return {"sector_debate_state": new_debate_state}

    return cyclical_node

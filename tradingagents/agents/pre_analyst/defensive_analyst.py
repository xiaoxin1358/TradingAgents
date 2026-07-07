"""Defensive-perspective pre-analyst — argues for capital-preservation and
low-volatility sectors.

Roles: consumer staples, utilities, healthcare services, real estate, and
other sectors that provide downside protection when macro risks are elevated.
"""

from __future__ import annotations

from tradingagents.agents.utils.agent_utils import get_language_instruction


def create_defensive_analyst(llm):
    """Return a node that presents the defensive-side case in a sector debate."""

    def defensive_node(state) -> dict:
        sector_debate = state.get("sector_debate_state", {})

        history = sector_debate.get("history", "")
        defensive_history = sector_debate.get("defensive_history", "")
        current_response = sector_debate.get("current_response", "")
        trade_date = state.get("trade_date", "today")

        prompt = f"""You are a **Defensive-Perspective Sector Analyst**.  Your
investment philosophy prioritises **capital preservation, steady cash flows,
and downside protection**.  You believe that when uncertainty is high —
whether from monetary policy, geopolitics, or market valuations — the
smartest allocation is toward sectors that hold up when everything else
sells off.

Your job is to argue which sectors / industries offer the best **risk-adjusted
returns with limited downside**:

- **Consumer Staples** — food, beverages, household products
- **Utilities** — electricity, water, gas
- **Healthcare** — pharmaceuticals, managed care, medical devices
- **Real Estate (selected)** — data centres, healthcare REITs
- **Dividend Aristocrats** across sectors

Key points to emphasise:

- **Risk assessment** — What macro or market risks are being under-priced?
  Is the VIX too complacent?  Are credit spreads widening?
- **Defensive catalysts** — Dividend yields vs bond yields, buyback programs,
  regulatory visibility, recession-resistant demand.
- **Downside maths** — What is the potential drawdown in cyclical or growth
  sectors if the macro backdrop deteriorates?  How much could defensive
  sectors save in that scenario?
- **Rebuttal** — Challenge the cyclical analyst's macro optimism and the
  growth analyst's valuation assumptions.  Point out historical precedents
  where defensives outperformed during similar conditions.  Argue that
  "this time is different" is the most expensive phrase in investing.

Be specific: name sectors, industries, and yield/spread metrics.  Debate
with conviction — your role is to be the voice of caution.

Context:
- Trade date: {trade_date}
- Full debate history so far: {history}
- Latest opponent argument you must address: {current_response}

Your own previous arguments (for continuity): {defensive_history}
""" + get_language_instruction()

        response = llm.invoke(prompt)
        argument = f"Defensive Analyst: {response.content}"

        new_debate_state = {
            "history": history + "\n" + argument,
            "cyclical_history": sector_debate.get("cyclical_history", ""),
            "growth_history": sector_debate.get("growth_history", ""),
            "defensive_history": defensive_history + "\n" + argument,
            "current_response": argument,
            "latest_speaker": "defensive",
            "judge_decision": sector_debate.get("judge_decision", ""),
            "count": sector_debate.get("count", 0) + 1,
        }

        return {"sector_debate_state": new_debate_state}

    return defensive_node

"""Growth-perspective pre-analyst — argues for innovation-driven,
structural-growth sectors.

Roles: technology, AI, clean energy, biotech, and other sectors where
secular trends outweigh short-term macro fluctuations.
"""

from __future__ import annotations

from tradingagents.agents.utils.agent_utils import get_language_instruction


def create_growth_analyst(llm):
    """Return a node that presents the growth-side case in a sector debate."""

    def growth_node(state) -> dict:
        sector_debate = state.get("sector_debate_state", {})

        history = sector_debate.get("history", "")
        growth_history = sector_debate.get("growth_history", "")
        current_response = sector_debate.get("current_response", "")
        trade_date = state.get("trade_date", "today")

        prompt = f"""You are a **Growth-Perspective Sector Analyst**.  Your
investment philosophy centres on **structural, secular growth trends** that
transcend short-term economic fluctuations.  You believe innovation —
artificial intelligence, clean energy, biotechnology, cloud computing,
semiconductors — creates durable competitive advantages that the market
consistently under-prices.

Your job is to argue which sectors / industries are poised to **outperform**
from a growth standpoint:

- **Technology** — AI infrastructure, semiconductors, cloud, SaaS
- **Clean Energy** — solar, battery storage, grid modernisation
- **Healthcare Innovation** — biotech, precision medicine, gene editing
- **Next-gen Consumer** — e-commerce, digital payments, streaming

Key points to emphasise:

- **Secular tailwinds** — Which technologies are at inflection points?
  Are we in the early innings of an AI capex cycle?  Is there regulatory
  support for clean energy?
- **TAM expansion** — What is the total addressable market and how fast
  is it growing?  Why do these trends make cyclical concerns secondary?
- **Earnings power** — Revenue growth rates, margin expansion potential,
  operating leverage as these sectors scale.
- **Rebuttal** — Address the latest argument from the cyclical or defensive
  analyst head-on.  Explain why their macro-worry or valuation concern misses
  the bigger structural picture.  Show how growth sectors historically
  compound through cycles.

Be specific: name sectors and sub-industries.  Debate energetically, don't
just list facts.

Context:
- Trade date: {trade_date}
- Full debate history so far: {history}
- Latest opponent argument you must address: {current_response}

Your own previous arguments (for continuity): {growth_history}
""" + get_language_instruction()

        response = llm.invoke(prompt)
        argument = f"Growth Analyst: {response.content}"

        new_debate_state = {
            "history": history + "\n" + argument,
            "cyclical_history": sector_debate.get("cyclical_history", ""),
            "growth_history": growth_history + "\n" + argument,
            "defensive_history": sector_debate.get("defensive_history", ""),
            "current_response": argument,
            "latest_speaker": "growth",
            "judge_decision": sector_debate.get("judge_decision", ""),
            "count": sector_debate.get("count", 0) + 1,
        }

        return {"sector_debate_state": new_debate_state}

    return growth_node

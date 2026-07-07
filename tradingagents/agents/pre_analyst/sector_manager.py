"""Sector Manager — reads the three-way sector debate and delivers a
structured sector-recommendation for downstream agents.

Uses the deep-thinking LLM (same pattern as Research Manager and Portfolio
Manager).  Produces a natural-language recommendation that includes:
recommended sectors, conviction level, rationale, and risk caveats.
"""

from __future__ import annotations

from tradingagents.agents.utils.agent_utils import get_language_instruction


def create_sector_manager(llm):
    """Return a node that judges the sector debate and issues a recommendation."""

    def sector_manager_node(state) -> dict:
        sector_debate = state.get("sector_debate_state", {})
        history = sector_debate.get("history", "")
        trade_date = state.get("trade_date", "today")

        prompt = f"""You are the **Sector Manager**, responsible for evaluating
a three-way debate among sector analysts and delivering a clear, actionable
sector recommendation for the investment team.

The three debaters represent different investment philosophies:
- **Cyclical Analyst** — favours macro-sensitive sectors (industrials, energy,
  financials, materials) based on the economic cycle.
- **Growth Analyst** — favours innovation-driven sectors (technology, AI,
  clean energy, biotech) based on secular trends.
- **Defensive Analyst** — favours capital-preservation sectors (staples,
  utilities, healthcare) based on risk management.

---

**Your Task:**

1. Read the full debate transcript below.
2. Evaluate the strength of each debater's arguments — their evidence,
   logic, and ability to rebut opponents.
3. Decide which perspective (or blend of perspectives) is most compelling
   for the current date: **{trade_date}**.
4. Issue a structured recommendation covering:

---

**Output format:**

## Sector Recommendation

### Preferred Sectors (ranked, with brief rationale)
1. **Sector name** — 1-2 sentences why
2. ...

### Sectors to Underweight / Avoid
- **Sector name** — brief reason
- ...

### Conviction Level
- High / Medium / Low — explain briefly

### Key Assumptions & Risks
- What needs to go right for this call to work?
- What could go wrong (and how to monitor)?

### Summary
- 2-3 sentence executive summary for the Portfolio Manager

---

**Debate Transcript:**
{history}
""" + get_language_instruction()

        response = llm.invoke(prompt)
        decision = response.content

        new_debate_state = {
            "history": history,
            "cyclical_history": sector_debate.get("cyclical_history", ""),
            "growth_history": sector_debate.get("growth_history", ""),
            "defensive_history": sector_debate.get("defensive_history", ""),
            "current_response": decision,
            "latest_speaker": "sector_manager",
            "judge_decision": decision,
            "count": sector_debate.get("count", 0),
        }

        return {
            "sector_debate_state": new_debate_state,
            "sector_recommendation": decision,
        }

    return sector_manager_node

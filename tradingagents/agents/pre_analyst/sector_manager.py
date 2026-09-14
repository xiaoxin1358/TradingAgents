"""Sector Manager — reads the three pre-analyst reports and delivers a
structured sector-recommendation for downstream agents.

Uses the deep-thinking LLM (same pattern as Research Manager and Portfolio
Manager).  Produces a natural-language recommendation that includes:
recommended sectors, conviction level, rationale, and risk caveats.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_global_news,
    get_language_instruction,
    get_prediction_markets,
)


def create_sector_manager(llm):
    """Return a node that synthesises the three pre-analyst reports into a
    sector recommendation."""

    def sector_manager_node(state) -> dict:
        current_date = state["trade_date"]

        cyclical_report = state.get("cyclical_report", "")
        growth_report = state.get("growth_report", "")
        defensive_report = state.get("defensive_report", "")

        tools = [get_global_news, get_prediction_markets]

        system_message = f"""You are the **Sector Manager**, responsible for synthesising
three independent sector-analysis reports and delivering a clear, actionable
sector recommendation for the investment team.

The three analysts represent different investment philosophies:
- **Cyclical Analyst** — favours macro-sensitive sectors (industrials, energy,
  financials, materials) based on the economic cycle.
- **Growth Analyst** — favours innovation-driven sectors (technology, AI,
  clean energy, biotech) based on secular trends.
- **Defensive Analyst** — favours capital-preservation sectors (staples,
  utilities, healthcare) based on risk management.

---

**Your Task:**

1. Use the available tools to verify any specific data points or supplement
   the reports with additional context.  If a tool returns an error or
   DATA_UNAVAILABLE, accept it and proceed.
2. Read the three reports below carefully.
3. Evaluate each analyst's evidence, logic, and risk assessment.
4. Decide which perspective (or blend of perspectives) is most compelling
   for the current date: **{current_date}**.
5. Issue a structured recommendation.

---

**Three Analyst Reports:**

### Cyclical Analyst Report
{cyclical_report}

### Growth Analyst Report
{growth_report}

### Defensive Analyst Report
{defensive_report}

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
""" + get_language_instruction()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " You have access to the following tools: {tool_names}."
                    " Today's date is {trade_date}; treat it as 'now' for all analysis and tool-call date ranges."
                    "\n{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(trade_date=current_date)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        recommendation = ""
        if len(result.tool_calls) == 0:
            recommendation = result.content

        return {
            "messages": [result],
            "sector_recommendation": recommendation,
        }

    return sector_manager_node

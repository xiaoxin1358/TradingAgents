"""Cyclical-perspective pre-analyst — analyses macro-sensitive sectors.

Roles: interest-rate cycle, inflation, industrial / energy / financial
sector rotation.  Produces a ``cyclical_report`` consumed by the Sector Manager.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_global_news,
    get_language_instruction,
    get_macro_indicators,
)


def create_cyclical_analyst(llm):
    """Return a node that analyses sectors from a cyclical / macro standpoint."""

    def cyclical_node(state) -> dict:
        current_date = state["trade_date"]

        tools = [get_global_news, get_macro_indicators]

        system_message = f"""You are a **Cyclical-Perspective Sector Analyst**.  Your
investment philosophy is grounded in macroeconomic cycles: interest-rate
trends, inflation dynamics, industrial production, commodity prices, and
employment data drive sector rotation.

Your job is to analyse which sectors / industries are poised to
**outperform** from a cyclical standpoint.  Focus on sectors that benefit
from the current stage of the economic cycle:

- **Early-cycle**: financials, consumer discretionary, industrials
- **Mid-cycle**: technology, energy, materials
- **Late-cycle**: energy, materials, health care, consumer staples

Key points to cover in your report:

- **Macro context** — Where are we in the rate cycle?  Is inflation cooling
  or accelerating?  What is the yield-curve shape telling us?
- **Sector catalysts** — Earnings revisions, capex cycles, inventory
  restocking, commodity super-cycles, infrastructure spending.
- **Relative value** — Are cyclical sectors trading at a discount to
  defensives?  Is the market under-pricing a rebound?
- **Risks** — What macro scenarios would hurt cyclical sectors?

Be specific: name sectors and, where appropriate, representative industries
or ETFs.  Produce a structured, standalone report.

**Instructions** — Use the available tools to gather real macro data
(macro indicators, global news) BEFORE writing your report.  For
get_macro_indicators, pass ONLY exact aliases: cpi, core_pce, unemployment,
fed_funds_rate, 10y_treasury, yield_curve, real_gdp, vix, dollar_index,
consumer_sentiment.  For get_global_news, pass curr_date='{current_date}'.
If any tool returns an error or DATA_UNAVAILABLE, accept it and proceed.

Trade date: {current_date}
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

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "cyclical_report": report,
        }

    return cyclical_node

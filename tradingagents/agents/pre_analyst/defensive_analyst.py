"""Defensive-perspective pre-analyst — analyses capital-preservation and
low-volatility sectors.

Roles: consumer staples, utilities, healthcare services, real estate, and
other sectors that provide downside protection when macro risks are elevated.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_global_news,
    get_language_instruction,
    get_macro_indicators,
)


def create_defensive_analyst(llm):
    """Return a node that analyses sectors from a defensive / risk-management standpoint."""

    def defensive_node(state) -> dict:
        current_date = state["trade_date"]

        tools = [get_global_news, get_macro_indicators]

        system_message = f"""You are a **Defensive-Perspective Sector Analyst**.  Your
investment philosophy prioritises **capital preservation, steady cash flows,
and downside protection**.  You believe that when uncertainty is high —
whether from monetary policy, geopolitics, or market valuations — the
smartest allocation is toward sectors that hold up when everything else
sells off.

Your job is to analyse which sectors / industries offer the best **risk-adjusted
returns with limited downside**:

- **Consumer Staples** — food, beverages, household products
- **Utilities** — electricity, water, gas
- **Healthcare** — pharmaceuticals, managed care, medical devices
- **Real Estate (selected)** — data centres, healthcare REITs
- **Dividend Aristocrats** across sectors

Key points to cover in your report:

- **Risk assessment** — What macro or market risks are being under-priced?
  Is the VIX too complacent?  Are credit spreads widening?
- **Defensive catalysts** — Dividend yields vs bond yields, buyback programs,
  regulatory visibility, recession-resistant demand.
- **Downside maths** — What is the potential drawdown in cyclical or growth
  sectors if the macro backdrop deteriorates?  How much could defensive
  sectors save in that scenario?
- **Opportunities** — When might defensives be overlooked and undervalued?

Be specific: name sectors, industries, and yield/spread metrics.
Produce a structured, standalone report.

**Instructions** — Use the available tools to gather real data (macro
indicators like VIX and Treasury yields, global news) BEFORE writing your
report.  For get_macro_indicators, pass ONLY exact aliases: cpi, core_pce,
unemployment, fed_funds_rate, 10y_treasury, yield_curve, real_gdp, vix,
dollar_index, consumer_sentiment.  For get_global_news, pass
curr_date='{current_date}'.  If any tool returns an error or DATA_UNAVAILABLE,
accept it and proceed.

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
            "defensive_report": report,
        }

    return defensive_node

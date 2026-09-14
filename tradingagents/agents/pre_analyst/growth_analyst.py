"""Growth-perspective pre-analyst — analyses innovation-driven,
structural-growth sectors.

Roles: technology, AI, clean energy, biotech, and other sectors where
secular trends outweigh short-term macro fluctuations.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_global_news,
    get_language_instruction,
    get_prediction_markets,
)


def create_growth_analyst(llm):
    """Return a node that analyses sectors from a growth / innovation standpoint."""

    def growth_node(state) -> dict:
        current_date = state["trade_date"]

        tools = [get_global_news, get_prediction_markets]

        system_message = f"""You are a **Growth-Perspective Sector Analyst**.  Your
investment philosophy centres on **structural, secular growth trends** that
transcend short-term economic fluctuations.  You believe innovation —
artificial intelligence, clean energy, biotechnology, cloud computing,
semiconductors — creates durable competitive advantages that the market
consistently under-prices.

Your job is to analyse which sectors / industries are poised to **outperform**
from a growth standpoint:

- **Technology** — AI infrastructure, semiconductors, cloud, SaaS
- **Clean Energy** — solar, battery storage, grid modernisation
- **Healthcare Innovation** — biotech, precision medicine, gene editing
- **Next-gen Consumer** — e-commerce, digital payments, streaming

Key points to cover in your report:

- **Secular tailwinds** — Which technologies are at inflection points?
  Are we in the early innings of an AI capex cycle?  Is there regulatory
  support for clean energy?
- **TAM expansion** — What is the total addressable market and how fast
  is it growing?  Why do these trends make cyclical concerns secondary?
- **Earnings power** — Revenue growth rates, margin expansion potential,
  operating leverage as these sectors scale.
- **Risks** — Valuation risk, regulatory risk, competitive disruption.

Be specific: name sectors and sub-industries.  Produce a structured,
standalone report.

**Instructions** — Use the available tools to gather real data (global news,
prediction-market probabilities) BEFORE writing your report.  For
get_prediction_markets, pass short topic keywords (e.g. 'Fed rate cut', 'AI',
'recession').  For get_global_news, pass curr_date='{current_date}'.
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
            "growth_report": report,
        }

    return growth_node

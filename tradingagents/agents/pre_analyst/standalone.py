"""Standalone entry-point for the pre-analyst sector debate.

This module builds a lightweight LangGraph StateGraph that runs the
three-way sector debate (Cyclical → Growth → Defensive → ... → Sector
Manager) **without** depending on the full ``TradingAgentsGraph`` or
the 12-agent pipeline.

Usage::

    python -m tradingagents.agents.pre_analyst.standalone

Or programmatically::

    from tradingagents.agents.pre_analyst.standalone import run_sector_analysis
    result = run_sector_analysis(provider="openai", model="gpt-4o")
    print(result["sector_recommendation"])
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from tradingagents.agents.pre_analyst import (
    SectorDebateState,
    create_cyclical_analyst,
    create_defensive_analyst,
    create_growth_analyst,
    create_sector_manager,
)
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.llm_clients.factory import create_llm_client

load_dotenv()


# ── lightweight conditional routing (no dependency on graph/conditional_logic) ──
def _should_continue_sector_debate(state: AgentState, max_rounds: int = 1) -> str:
    sector_state = state.get("sector_debate_state", {})
    count = sector_state.get("count", 0)

    if count >= 3 * max_rounds:
        return "Sector Manager"

    latest = sector_state.get("latest_speaker", "")
    if latest == "cyclical":
        return "Growth Analyst"
    if latest == "growth":
        return "Defensive Analyst"
    return "Cyclical Analyst"


def _build_standalone_graph(
    llm: Any,
    max_debate_rounds: int = 1,
) -> Any:
    """Build a minimal StateGraph for the sector debate only."""
    quick_llm = llm
    deep_llm = llm  # standalone: single LLM for simplicity

    workflow = StateGraph(AgentState)

    workflow.add_node("Cyclical Analyst", create_cyclical_analyst(quick_llm))
    workflow.add_node("Growth Analyst", create_growth_analyst(quick_llm))
    workflow.add_node("Defensive Analyst", create_defensive_analyst(quick_llm))
    workflow.add_node("Sector Manager", create_sector_manager(deep_llm))

    workflow.add_edge(START, "Cyclical Analyst")

    for node_name, routes in [
        (
            "Cyclical Analyst",
            {"Growth Analyst": "Growth Analyst", "Defensive Analyst": "Defensive Analyst", "Sector Manager": "Sector Manager"},
        ),
        (
            "Growth Analyst",
            {"Cyclical Analyst": "Cyclical Analyst", "Defensive Analyst": "Defensive Analyst", "Sector Manager": "Sector Manager"},
        ),
        (
            "Defensive Analyst",
            {"Cyclical Analyst": "Cyclical Analyst", "Growth Analyst": "Growth Analyst", "Sector Manager": "Sector Manager"},
        ),
    ]:
        workflow.add_conditional_edges(
            node_name,
            lambda s, mr=max_debate_rounds: _should_continue_sector_debate(s, mr),
            routes,
        )

    workflow.add_edge("Sector Manager", END)

    return workflow.compile()


def run_sector_analysis(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    max_debate_rounds: int = 1,
) -> dict[str, Any]:
    """Run the pre-analyst sector debate and return the recommendation.

    Args:
        provider: LLM provider key (e.g. "openai", "deepseek").  Defaults to
            ``TRADINGAGENTS_LLM_PROVIDER`` env var or ``DEFAULT_CONFIG``.
        model: Model name.  Defaults to the quick-thinking model from config.
        base_url: Optional API endpoint override.
        max_debate_rounds: How many full 3-speaker rotations to run (default 1).

    Returns:
        dict with keys ``sector_recommendation``, ``debate_history``,
        ``judge_decision``.
    """
    if provider is None:
        provider = os.environ.get("TRADINGAGENTS_LLM_PROVIDER", DEFAULT_CONFIG["llm_provider"])
    if model is None:
        model = DEFAULT_CONFIG["quick_think_llm"]

    client = create_llm_client(provider, model, base_url)
    llm = client.get_llm()

    graph = _build_standalone_graph(llm, max_debate_rounds)

    trade_date = datetime.now().strftime("%Y-%m-%d")

    initial_state: dict[str, Any] = {
        "messages": [("human", "Analyse which sectors / industries have the best investment potential right now.")],
        "company_of_interest": "Sector Analysis",
        "trade_date": trade_date,
        "sector_debate_state": SectorDebateState(
            cyclical_history="",
            growth_history="",
            defensive_history="",
            history="",
            current_response="",
            latest_speaker="",
            judge_decision="",
            count=0,
        ),
        "sector_recommendation": "",
    }

    final_state = graph.invoke(initial_state, {"recursion_limit": 100})

    return {
        "sector_recommendation": final_state.get("sector_recommendation", ""),
        "debate_history": final_state.get("sector_debate_state", {}).get("history", ""),
        "judge_decision": final_state.get("sector_debate_state", {}).get("judge_decision", ""),
    }


# ── CLI entry-point ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the pre-analyst sector debate standalone.")
    parser.add_argument("--provider", default=None, help="LLM provider (e.g. openai, deepseek)")
    parser.add_argument("--model", default=None, help="Model name")
    parser.add_argument("--base-url", default=None, help="API base URL override")
    parser.add_argument("--rounds", type=int, default=1, help="Number of full debate rotations")
    args = parser.parse_args()

    print("Running pre-analyst sector debate ...")
    result = run_sector_analysis(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        max_debate_rounds=args.rounds,
    )

    print("\n" + "=" * 60)
    print(result["sector_recommendation"])
    print("=" * 60)

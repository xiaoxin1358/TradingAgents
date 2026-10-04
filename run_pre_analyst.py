"""Pre-Analyst sector analysis pipeline (standalone -- no main analysts).

Usage:
    python run_pre_analyst.py
    python run_pre_analyst.py --ticker SPY --date 2026-07-16
    python run_pre_analyst.py --provider deepseek --model deepseek-v4-pro

Builds a minimal LangGraph pipeline:
    Cyclical -> Growth -> Defensive -> Sector Manager -> END

Results are saved under ``reports/pre_analyst_<timestamp>/``.
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler
from langgraph.graph import END, START, StateGraph

from tradingagents.agents.pre_analyst import (
    create_cyclical_analyst,
    create_defensive_analyst,
    create_growth_analyst,
    create_sector_manager,
)
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import (
    create_msg_delete,
    get_global_news,
    get_macro_indicators,
    get_prediction_markets,
)
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.llm_clients import create_llm_client
from tradingagents.reporting import write_sector_report

# ==================================================================
# Logging callback -- records every LLM call and tool execution
# ==================================================================

logging.basicConfig(
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("pre_analyst")


class PreAnalystLogger(BaseCallbackHandler):
    """Lightweight callback: logs LLM invocations and tool calls with timing."""

    def __init__(self):
        super().__init__()
        self._llm_timers: dict[int, float] = {}
        self._call_idx = 0

    # -- LLM events --------------------------------------------------

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._call_idx += 1
        idx = self._call_idx
        self._llm_timers[idx] = time.perf_counter()

        model = serialized.get("kwargs", {}).get("model", "?")
        prompt_len = sum(len(p) for p in prompts)
        logger.info("[LLM #%d] start  |  model=%s  |  prompt_length=%d", idx, model, prompt_len)

    def on_llm_end(self, response, **kwargs):
        idx = self._call_idx
        elapsed = time.perf_counter() - self._llm_timers.pop(idx, 0)

        msg = response.generations[0][0].message
        content_len = len(msg.content) if msg.content else 0
        tc_count = len(msg.tool_calls) if msg.tool_calls else 0
        usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}

        parts = [f"[LLM #{idx}] done  |  time={elapsed:.1f}s  |  output_len={content_len}"]
        if tc_count:
            tool_names = [tc.get("name", "?") for tc in msg.tool_calls]
            parts.append(f"tool_calls={tc_count} ({', '.join(tool_names)})")
        if usage:
            parts.append(f"tokens={usage.get('total_tokens', '?')} (in={usage.get('prompt_tokens', '?')} out={usage.get('completion_tokens', '?')})")
        logger.info("  ".join(parts))

    def on_llm_error(self, error, **kwargs):
        idx = self._call_idx
        logger.error("[LLM #%d] ERROR  |  %s", idx, error)

    # -- Tool events -------------------------------------------------

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "?")
        inp = input_str if len(input_str) <= 200 else input_str[:200] + "..."
        logger.info("[TOOL]  %s  |  input=%s", tool_name, inp)

    def on_tool_end(self, output, **kwargs):
        out = output if len(output) <= 300 else output[:300] + "..."
        out_one_line = out.replace("\n", " ")
        logger.info("[TOOL]  done  |  output=%s", out_one_line)

    def on_tool_error(self, error, **kwargs):
        logger.warning("[TOOL]  ERROR  |  %s", error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-Analyst: Sector Analysis Pipeline")
    parser.add_argument("--ticker", default="SPY", help="Ticker symbol (default: SPY)")
    parser.add_argument("--date", default=None, help="Trade date YYYY-MM-DD (default: today)")
    parser.add_argument("--provider", default=None, help="LLM provider override")
    parser.add_argument("--model", default=None, help="Model name override")
    parser.add_argument("--base-url", default=None, help="API base URL override")
    args = parser.parse_args()

    trade_date = args.date or datetime.now().strftime("%Y-%m-%d")

    config = DEFAULT_CONFIG.copy()
    if args.provider:
        config["llm_provider"] = args.provider
    if args.model:
        config["quick_think_llm"] = args.model
        config["deep_think_llm"] = args.model
    if args.base_url:
        config["backend_url"] = args.base_url

    print("=" * 60)
    print("  Pre-Analyst: Industry Sector Analysis Pipeline")
    print(f"  Ticker: {args.ticker}  |  Date: {trade_date}")
    print(f"  Provider: {config['llm_provider']}  |  Model: {config['quick_think_llm']}")
    print("=" * 60)

    # -- Callback ---------------------------------------------------
    callback = PreAnalystLogger()

    # -- Create LLMs -------------------------------------------------
    quick_client = create_llm_client(
        provider=config["llm_provider"],
        model=config["quick_think_llm"],
        base_url=config.get("backend_url"),
        callbacks=[callback],
    )
    deep_client = create_llm_client(
        provider=config["llm_provider"],
        model=config["deep_think_llm"],
        base_url=config.get("backend_url"),
        callbacks=[callback],
    )
    quick_llm = quick_client.get_llm()
    deep_llm = deep_client.get_llm()

    # -- ToolNodes ---------------------------------------------------
    from langgraph.prebuilt import ToolNode

    tool_nodes = {
        "cyclical": ToolNode([get_global_news, get_macro_indicators]),
        "growth": ToolNode([get_global_news, get_prediction_markets]),
        "defensive": ToolNode([get_global_news, get_macro_indicators]),
        "sector_manager": ToolNode([get_global_news, get_prediction_markets]),
    }

    # -- Build minimal pre-analyst graph -----------------------------
    workflow = StateGraph(AgentState)

    workflow.add_node("Cyclical Analyst", create_cyclical_analyst(quick_llm))
    workflow.add_node("Growth Analyst", create_growth_analyst(quick_llm))
    workflow.add_node("Defensive Analyst", create_defensive_analyst(quick_llm))
    workflow.add_node("Sector Manager", create_sector_manager(deep_llm))

    workflow.add_node("tools_cyclical", tool_nodes["cyclical"])
    workflow.add_node("tools_growth", tool_nodes["growth"])
    workflow.add_node("tools_defensive", tool_nodes["defensive"])
    workflow.add_node("tools_sector_manager", tool_nodes["sector_manager"])

    workflow.add_node("Msg Clear Cyclical", create_msg_delete())
    workflow.add_node("Msg Clear Growth", create_msg_delete())
    workflow.add_node("Msg Clear Defensive", create_msg_delete())
    workflow.add_node("Msg Clear Sector", create_msg_delete())

    # -- Edges -------------------------------------------------------
    def _should_continue(state: AgentState, tool_key: str, clear_key: str) -> str:
        """Route to tool node if tool_calls present, else Msg Clear."""
        last = state["messages"][-1]
        return tool_key if last.tool_calls else clear_key

    workflow.add_edge(START, "Cyclical Analyst")

    for analyst, tool_node, clear_node, next_node in (
        ("Cyclical Analyst", "tools_cyclical", "Msg Clear Cyclical", "Growth Analyst"),
        ("Growth Analyst", "tools_growth", "Msg Clear Growth", "Defensive Analyst"),
        ("Defensive Analyst", "tools_defensive", "Msg Clear Defensive", "Sector Manager"),
        ("Sector Manager", "tools_sector_manager", "Msg Clear Sector", END),
    ):
        workflow.add_conditional_edges(
            analyst,
            lambda s, tn=tool_node, cn=clear_node: _should_continue(s, tn, cn),
            [tool_node, clear_node],
        )
        workflow.add_edge(tool_node, analyst)
        workflow.add_edge(clear_node, next_node)

    graph = workflow.compile()

    # -- Run ---------------------------------------------------------
    initial_state = {
        "messages": [("human", f"Analyze sector-level conditions for {args.ticker}.")],
        "company_of_interest": args.ticker,
        "trade_date": trade_date,
        "cyclical_report": "",
        "growth_report": "",
        "defensive_report": "",
        "sector_recommendation": "",
    }

    print("\nRunning pre-analyst pipeline...\n")
    final_state = graph.invoke(
        initial_state,
        {"recursion_limit": 100, "callbacks": [callback]},
    )

    # -- Report ------------------------------------------------------
    report_dir = Path("reports") / f"pre_analyst_{datetime.now():%Y%m%d_%H%M%S}"
    result = {
        "cyclical_report": final_state.get("cyclical_report", ""),
        "growth_report": final_state.get("growth_report", ""),
        "defensive_report": final_state.get("defensive_report", ""),
        "sector_recommendation": final_state.get("sector_recommendation", ""),
    }
    report_path = write_sector_report(result, report_dir)
    print(f"\nReport saved: {report_path.resolve()}")

    print("\n" + "=" * 60)
    recommendation = final_state.get("sector_recommendation", "")
    if recommendation:
        print(recommendation)
    else:
        print("(Sector Manager did not produce a recommendation -- check LLM logs.)")
    print("=" * 60)

"""Web API backend for TradingAgents (docs/vue-frontend.md, M1 read-only).

Reads the reports/ tree and contradictions.db WITHOUT importing the
tradingagents package or any LLM client — fast startup, zero side effects.
"""

__all__ = ["main"]

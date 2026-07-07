"""Pre-Analyst module — sector / industry debate agents.

These agents run *before* the per-ticker analyst pipeline to identify
which sectors or industries have the best risk-adjusted potential given
the current macroeconomic backdrop.  The output (``sector_recommendation``)
is injected into the ``AgentState`` for downstream agents to consume.
"""

from .cyclical_analyst import create_cyclical_analyst
from .defensive_analyst import create_defensive_analyst
from .growth_analyst import create_growth_analyst
from .sector_debate_state import SectorDebateState
from .sector_manager import create_sector_manager

__all__ = [
    "SectorDebateState",
    "create_cyclical_analyst",
    "create_defensive_analyst",
    "create_growth_analyst",
    "create_sector_manager",
]

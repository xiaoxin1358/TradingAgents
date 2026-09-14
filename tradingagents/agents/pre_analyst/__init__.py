"""Pre-Analyst module — sector / industry pipeline agents.

These agents run *before* the per-ticker analyst pipeline to identify
which sectors or industries have the best risk-adjusted potential given
the current macroeconomic backdrop.  Each analyst produces a dedicated
report field on ``AgentState``; the Sector Manager synthesises them into
``sector_recommendation`` for downstream consumption.
"""

from .cyclical_analyst import create_cyclical_analyst
from .defensive_analyst import create_defensive_analyst
from .growth_analyst import create_growth_analyst
from .sector_manager import create_sector_manager

__all__ = [
    "create_cyclical_analyst",
    "create_defensive_analyst",
    "create_growth_analyst",
    "create_sector_manager",
]

"""State schema for the sector-industry debate among pre-analysts.

Mirrors the pattern of ``InvestDebateState`` and ``RiskDebateState`` in
``agent_states.py`` but scoped to the three-way sector debate (cyclical /
growth / defensive) that runs before the per-ticker analyst pipeline.
"""

from typing import Annotated

from typing_extensions import TypedDict


class SectorDebateState(TypedDict):
    """Debate state for the three-way sector-industry discussion.

    Three analysts take turns arguing which sectors / industries have the
    best risk-adjusted potential given the current macro backdrop.  The
    sector manager reads the full debate history and issues a final
    sector recommendation that downstream agents can consume.
    """

    cyclical_history: Annotated[
        str, "Cyclical-perspective analyst's running argument log"
    ]
    growth_history: Annotated[
        str, "Growth-perspective analyst's running argument log"
    ]
    defensive_history: Annotated[
        str, "Defensive-perspective analyst's running argument log"
    ]
    history: Annotated[str, "Full debate transcript"]
    current_response: Annotated[str, "Most recent argument (any side)"]
    latest_speaker: Annotated[
        str, "Who spoke last: 'cyclical', 'growth', or 'defensive'"
    ]
    judge_decision: Annotated[str, "Sector Manager's final recommendation"]
    count: Annotated[int, "Total number of speeches so far"]

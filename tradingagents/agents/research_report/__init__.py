"""Research report reading agents — independent from the main trading pipeline.

v2.0: Data Loader pre-fetches → 5 parallel pure-LLM Readers → Summary Manager.
"""

from .claim_extractor import create_claim_extractor
from .contradiction_judge import create_contradiction_judge
from .contradiction_report import (
    create_contradiction_insight,
    create_contradiction_report,
)
from .contradiction_store import ContradictionStore, contradiction_id
from .industry_reader import create_industry_reader
from .macro_reader import create_macro_reader
from .morning_reader import create_morning_reader
from .state import ResearchReportState
from .stock_reader import create_stock_reader
from .strategy_reader import create_strategy_reader
from .summary_manager import create_summary_manager
from .tools import load_all_reports, read_report_folder

__all__ = [
    "create_claim_extractor",
    "create_contradiction_insight",
    "create_contradiction_judge",
    "create_contradiction_report",
    "ContradictionStore",
    "contradiction_id",
    "create_industry_reader",
    "create_macro_reader",
    "create_morning_reader",
    "create_stock_reader",
    "create_strategy_reader",
    "create_summary_manager",
    "load_all_reports",
    "read_report_folder",
    "ResearchReportState",
]

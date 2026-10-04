"""Look-ahead filter for yfinance financial statements.

``filter_financials_by_date`` drops fiscal-period columns after ``curr_date``
so a historical run does not see statements that had not been filed yet.
"""

from __future__ import annotations

import pandas as pd
import pytest

from tradingagents.dataflows.stockstats_utils import filter_financials_by_date


@pytest.mark.unit
def test_filter_financials_drops_periods_after_curr_date():
    # yfinance statement frames use fiscal period-end timestamps as columns.
    frame = pd.DataFrame(
        {
            pd.Timestamp("2024-09-30"): [100.0, 40.0],
            pd.Timestamp("2024-06-30"): [90.0, 35.0],
            pd.Timestamp("2023-12-31"): [80.0, 30.0],
        },
        index=["Total Revenue", "Net Income"],
    )

    filtered = filter_financials_by_date(frame, "2024-06-30")

    assert list(filtered.columns) == [
        pd.Timestamp("2024-06-30"),
        pd.Timestamp("2023-12-31"),
    ]
    assert list(filtered.index) == ["Total Revenue", "Net Income"]
    assert filtered.loc["Total Revenue", pd.Timestamp("2024-06-30")] == 90.0
    assert filtered.loc["Net Income", pd.Timestamp("2023-12-31")] == 30.0
    # The cutoff day itself stays; only later fiscal periods are removed.
    assert pd.Timestamp("2024-09-30") not in filtered.columns

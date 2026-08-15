"""Runnable checks for the M1 read-only web API (no HTTP server needed).

Covers the two risky bits: path-traversal hardening in the reports scanner
and the whitelisted contradiction queries against a temp SQLite db.
"""

import sqlite3
from pathlib import Path

from webapi import contradictions as ctr
from webapi.reports import ReportsRoot


def _make_db(db_path: Path) -> str:
    import json

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE contradictions (
            id TEXT PRIMARY KEY, subject TEXT NOT NULL, kind TEXT NOT NULL,
            scope TEXT NOT NULL, scale TEXT NOT NULL, claim_a TEXT NOT NULL,
            claim_b TEXT NOT NULL, horizon_a TEXT, horizon_b TEXT,
            status TEXT NOT NULL DEFAULT 'open', winner TEXT, resolved_by TEXT,
            resolved_date TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
            insight TEXT
        );
        """
    )
    a = {"broker": "国元", "direction": 1, "quote": "看多"}
    b = {"broker": "中邮", "direction": -1, "quote": "看空"}
    insight = {"cause_type": "时间尺度", "tilt": "不确定"}
    conn.execute(
        "INSERT INTO contradictions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "AI|国元|中邮|opinion", "AI", "opinion", "direct", "same",
            json.dumps(a, ensure_ascii=False), json.dumps(b, ensure_ascii=False),
            None, None, "open", None, None, None, "2026-08-10", "2026-08-12",
            json.dumps(insight, ensure_ascii=False),
        ),
    )
    conn.execute(
        "INSERT INTO contradictions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "PPI|东吴|国信|factual", "PPI", "factual", "direct", "cross",
            json.dumps(a, ensure_ascii=False), json.dumps(b, ensure_ascii=False),
            None, None, "resolved", "a", "market", "2026-08-12",
            "2026-08-05", "2026-08-12", None,
        ),
    )
    conn.commit()
    conn.close()
    return str(db_path)


def test_scanner_blocks_path_traversal(tmp_path):
    root = ReportsRoot(tmp_path)
    (tmp_path / "SPY_20260801_120000").mkdir()
    assert root._safe_dir("../etc") is None
    assert root._safe_file("SPY_20260801_120000", "../etc/passwd") is None
    assert root._safe_file("SPY_20260801_120000", "1_analysts/../../x.md") is None
    assert root.daily_dates() == []
    assert len(root.trading_runs()) == 1


def test_scanner_lists_daily_dates_and_files(tmp_path):
    (tmp_path / "2026-08-13").mkdir()
    (tmp_path / "2026-08-13" / "final_summary.md").write_text("# hi", encoding="utf-8")
    root = ReportsRoot(tmp_path)
    assert root.daily_dates() == ["2026-08-13"]
    meta = root.daily_meta("2026-08-13")
    assert len(meta["files"]) == 7
    assert meta["files"][-2]["exists"]  # final_summary
    assert root.daily_file("2026-08-13", "final_summary.md") == "# hi"
    assert root.daily_file("2026-08-13", "../secret.md") is None


def test_contradiction_queries_and_filters(tmp_path):
    db = _make_db(tmp_path / "c.db")

    res = ctr.list_contradictions(db, status="open")
    assert res["total"] == 1
    row = res["rows"][0]
    assert row["subject"] == "AI"
    assert row["direction_a"] == "看多" and row["direction_b"] == "看空"
    assert row["days_open"] is not None and row["days_open"] >= 2

    by_cause = ctr.list_contradictions(db, cause_type="时间尺度")
    assert by_cause["total"] == 1

    by_subject = ctr.list_contradictions(db, subject="PPI")
    assert by_subject["total"] == 1 and by_subject["rows"][0]["status"] == "resolved"

    st = ctr.stats(db)
    assert st["total"] == 2 and st["open"] == 1 and st["resolved"] == 1
    assert st["resolve_rate"] == 50.0
    assert st["cause_dist"].get("时间尺度") == 1

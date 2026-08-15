"""Read-only SQLite access to reports/contradictions.db (v3.3 schema).

Queries are whitelisted: every filter is a bound parameter, never string
interpolation. The db is opened with mode=ro so the web layer can never
mutate the contradiction ledger.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

_DIRECTION = {-1: "看空", 0: "中性", 1: "看多"}
_KIND_CN = {"factual": "事实", "opinion": "观点"}
_SCOPE_CN = {"direct": "直接", "indirect": "间接"}
_SCALE_CN = {"same": "同尺度", "cross": "跨尺度"}

_COLS = [
    "id", "subject", "kind", "scope", "scale", "claim_a", "claim_b",
    "horizon_a", "horizon_b", "status", "winner", "resolved_by",
    "resolved_date", "first_seen", "last_seen", "insight",
]

_FILTER_COLS = {"status", "kind", "scope", "scale", "winner", "resolved_by"}


def _open_ro(db_path: str | Path) -> sqlite3.Connection:
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _days_open(row: dict, today: str) -> int | None:
    try:
        return (date.fromisoformat(today) - date.fromisoformat(row["first_seen"])).days
    except ValueError:
        return None


def _decorate(row: dict, today: str) -> dict:
    for key in ("claim_a", "claim_b"):
        try:
            row[key] = json.loads(row[key])
        except (TypeError, ValueError):
            row[key] = {}
    try:
        row["insight"] = json.loads(row["insight"])
    except (TypeError, ValueError):
        row["insight"] = None
    row["direction_a"] = _DIRECTION.get(row["claim_a"].get("direction"), "?")
    row["direction_b"] = _DIRECTION.get(row["claim_b"].get("direction"), "?")
    row["kind_cn"] = _KIND_CN.get(row.get("kind", "?"), row.get("kind", "?"))
    row["scope_cn"] = _SCOPE_CN.get(row.get("scope", "?"), row.get("scope", "?"))
    row["scale_cn"] = _SCALE_CN.get(row.get("scale", "?"), row.get("scale", "?"))
    row["days_open"] = _days_open(row, today)
    return row


def list_contradictions(
    db_path: str | Path,
    *,
    status: str | None = None,
    kind: str | None = None,
    scope: str | None = None,
    scale: str | None = None,
    subject: str | None = None,
    cause_type: str | None = None,
    min_days: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List rows + total count under the given filters (docs 6.2)."""
    if not Path(db_path).exists():
        return {"rows": [], "total": 0}
    where, params = [], []
    for col in _FILTER_COLS:
        if locals().get(col):
            where.append(f"{col}=?")
            params.append(locals()[col])
    if subject:
        where.append("subject LIKE ?")
        params.append(f"%{subject}%")
    if cause_type:
        where.append("json_extract(insight, '$.cause_type')=?")
        params.append(cause_type)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    conn = _open_ro(db_path)
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM contradictions {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT {', '.join(_COLS)} FROM contradictions {where_sql}"
            " ORDER BY last_seen DESC, first_seen DESC LIMIT ? OFFSET ?",
            [*params, min(max(limit, 1), 500), max(offset, 0)],
        ).fetchall()
    finally:
        conn.close()

    today = date.today().isoformat()
    out = []
    for r in rows:
        d = _decorate(dict(zip(_COLS, r)), today)
        if min_days is not None and (d["days_open"] is None or d["days_open"] < min_days):
            continue
        out.append(d)
    return {"rows": out, "total": total}


def get_contradiction(db_path: str | Path, cid: str) -> dict | None:
    if not Path(db_path).exists():
        return None
    conn = _open_ro(db_path)
    try:
        row = conn.execute(
            f"SELECT {', '.join(_COLS)} FROM contradictions WHERE id=?",
            (cid,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return _decorate(dict(zip(_COLS, row)), date.today().isoformat())


def stats(db_path: str | Path) -> dict:
    """v3.3 stats: totals + kind/cause_type distributions + longest open."""
    out = {"total": 0, "open": 0, "resolved": 0, "resolve_rate": 0.0,
           "kind_dist": {}, "cause_dist": {}, "longest_open": 0}
    if not Path(db_path).exists():
        return out
    conn = _open_ro(db_path)
    try:
        out["total"] = conn.execute("SELECT COUNT(*) FROM contradictions").fetchone()[0]
        out["open"] = conn.execute(
            "SELECT COUNT(*) FROM contradictions WHERE status='open'"
        ).fetchone()[0]
        out["resolved"] = out["total"] - out["open"]
        out["resolve_rate"] = (
            out["resolved"] / out["total"] * 100 if out["total"] else 0.0
        )
        out["kind_dist"] = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM contradictions WHERE status='open'"
            " GROUP BY kind"
        ).fetchall())
        rows = conn.execute(
            "SELECT insight, first_seen FROM contradictions WHERE status='open'"
        ).fetchall()
    finally:
        conn.close()

    today = date.today().isoformat()
    causes: dict[str, int] = {}
    longest = 0
    for raw, first_seen in rows:
        try:
            cause = json.loads(raw).get("cause_type", "其他") if raw else "未生成"
        except (TypeError, ValueError):
            cause = "未生成"
        causes[cause] = causes.get(cause, 0) + 1
        try:
            longest = max(longest, (date.fromisoformat(today) - date.fromisoformat(first_seen)).days)
        except ValueError:
            pass
    out["cause_dist"] = causes
    out["longest_open"] = longest
    return out

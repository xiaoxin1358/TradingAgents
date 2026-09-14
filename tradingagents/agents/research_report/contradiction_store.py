"""SQLite persistence for detected report contradictions (no LLM).

FR-3: contradictions are keyed by a deterministic id
``f"{subject}|{brokerA}|{brokerB}|{kind}"`` so the same broker pair on the
same subject reuses one row across days (``first_seen`` kept, ``last_seen``
refreshed). Connection style mirrors ``tradingagents/graph/checkpointer.py``.

FR-7: each row also carries an ``insight`` column (JSON from the deep-LLM
Contradiction Insight node) explaining the contradiction's root cause.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS contradictions (
    id           TEXT PRIMARY KEY,
    subject      TEXT NOT NULL,
    kind         TEXT NOT NULL,
    scope        TEXT NOT NULL,
    scale        TEXT NOT NULL,
    claim_a      TEXT NOT NULL,
    claim_b      TEXT NOT NULL,
    horizon_a    TEXT,
    horizon_b    TEXT,
    status       TEXT NOT NULL DEFAULT 'open',
    winner       TEXT,
    resolved_by  TEXT,
    resolved_date TEXT,
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL,
    insight      TEXT
);
CREATE INDEX IF NOT EXISTS idx_contradictions_status ON contradictions(status);
CREATE INDEX IF NOT EXISTS idx_contradictions_subject ON contradictions(subject);
"""

_COLS = [
    "id", "subject", "kind", "scope", "scale", "claim_a", "claim_b",
    "horizon_a", "horizon_b", "status", "winner", "resolved_by",
    "resolved_date", "first_seen", "last_seen", "insight",
]


def contradiction_id(claim_a: dict, claim_b: dict, subject: str, kind: str) -> str:
    """Deterministic id so the same pair + subject reuses one row across days."""
    brokers = sorted([claim_a.get("broker", "?"), claim_b.get("broker", "?")])
    return f"{subject}|{brokers[0]}|{brokers[1]}|{kind}"


class ContradictionStore:
    """Thin sqlite3 wrapper. All methods take/return plain dicts."""

    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        # 迁移：旧库（无 insight 列）补列；新库/已迁移库会抛 "duplicate column"
        try:
            self._conn.execute("ALTER TABLE contradictions ADD COLUMN insight TEXT")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass

    # ── write ──

    def upsert(self, item: dict, today: str) -> bool:
        """Insert a contradiction or refresh an existing one. True if newly inserted."""
        cid = item["id"]
        claim_a = json.dumps(item["claim_a"], ensure_ascii=False)
        claim_b = json.dumps(item["claim_b"], ensure_ascii=False)
        if self._conn.execute("SELECT 1 FROM contradictions WHERE id=?", (cid,)).fetchone():
            self._conn.execute(
                "UPDATE contradictions SET last_seen=?, claim_a=?, claim_b=?,"
                " horizon_a=?, horizon_b=? WHERE id=?",
                (today, claim_a, claim_b, item.get("horizon_a"), item.get("horizon_b"), cid),
            )
            self._conn.commit()
            return False
        self._conn.execute(
            "INSERT INTO contradictions (id, subject, kind, scope, scale, claim_a, claim_b,"
            " horizon_a, horizon_b, status, first_seen, last_seen)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (cid, item["subject"], item["kind"], item["scope"], item["scale"],
             claim_a, claim_b, item.get("horizon_a"), item.get("horizon_b"),
             "open", today, today),
        )
        self._conn.commit()
        return True

    def resolve(self, cid: str, winner: str, resolved_by: str, today: str) -> None:
        self._conn.execute(
            "UPDATE contradictions SET status='resolved', winner=?, resolved_by=?,"
            " resolved_date=? WHERE id=?",
            (winner, resolved_by, today, cid),
        )
        self._conn.commit()
    def save_insight(self, cid: str, insight: dict) -> None:
        """FR-7: persist the deep-LLM insight JSON for one contradiction."""
        self._conn.execute(
            "UPDATE contradictions SET insight=? WHERE id=?",
            (json.dumps(insight, ensure_ascii=False), cid),
        )
        self._conn.commit()
    # ── read ──

    def _rows(self, where: str, params: tuple) -> list[dict]:
        rows = self._conn.execute(
            f"SELECT {', '.join(_COLS)} FROM contradictions {where}", params
        ).fetchall()
        out = []
        for r in rows:
            d = dict(zip(_COLS, r))
            d["claim_a"] = json.loads(d["claim_a"])
            d["claim_b"] = json.loads(d["claim_b"])
            out.append(d)
        return out

    def list_open(self) -> list[dict]:
        return self._rows("WHERE status='open' ORDER BY last_seen DESC", ())

    def new_since(self, day: str) -> list[dict]:
        return self._rows("WHERE first_seen=? ORDER BY last_seen DESC", (day,))

    def resolved_since(self, day: str) -> list[dict]:
        return self._rows(
            "WHERE status='resolved' AND resolved_date=? ORDER BY resolved_date DESC", (day,)
        )

    def list_summary(self, limit: int = 100) -> str:
        """Compact JSON of open contradictions, fed to the Judge for context."""
        rows = self._conn.execute(
            "SELECT subject, kind, scope, scale, claim_a, claim_b, first_seen, last_seen"
            " FROM contradictions WHERE status='open' ORDER BY last_seen DESC LIMIT ?",
            (limit,),
        ).fetchall()
        summary = []
        for subject, kind, scope, scale, claim_a, claim_b, first_seen, last_seen in rows:
            a, b = json.loads(claim_a), json.loads(claim_b)
            summary.append({
                "subject": subject, "kind": kind, "scope": scope, "scale": scale,
                "broker_a": a.get("broker"), "broker_b": b.get("broker"),
                "first_seen": first_seen, "last_seen": last_seen,
            })
        return json.dumps(summary, ensure_ascii=False)

    def stats(self) -> dict:
        total = self._conn.execute("SELECT COUNT(*) FROM contradictions").fetchone()[0]
        open_ = self._conn.execute(
            "SELECT COUNT(*) FROM contradictions WHERE status='open'"
        ).fetchone()[0]
        resolved = self._conn.execute(
            "SELECT COUNT(*) FROM contradictions WHERE status='resolved'"
        ).fetchone()[0]
        return {"total": total, "open": open_, "resolved": resolved}

    def close(self) -> None:
        self._conn.close()

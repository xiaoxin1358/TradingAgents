"""Safe read-only scanner for the reports/ tree.

Path rules (docs/vue-frontend.md 6.4): every path segment must match
``^[A-Za-z0-9._-]{1,128}$`` and the resolved path must stay inside the
reports root (path-traversal hardening, same spirit as the CLI ticker check).
"""

from __future__ import annotations

import re
from pathlib import Path

_SEG_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TRADING_RE = re.compile(r"^[A-Za-z0-9.-]+_\d{8}_\d{6}$")  # TICKER_YYYYMMDD_HHMMSS
_PRE_RE = re.compile(r"^pre_analyst_\d{8}_\d{6}$")

# The 7 files a daily research-report run produces (docs 2.1).
DAILY_FILES = [
    "macro_summary.md",
    "industry_summary.md",
    "stock_summary.md",
    "strategy_summary.md",
    "morning_summary.md",
    "final_summary.md",
    "contradiction_report.md",
]

# Display names for the daily report tabs (docs 5.3).
DAILY_LABELS = {
    "macro_summary.md": "宏观研究",
    "industry_summary.md": "行业研报",
    "stock_summary.md": "个股研报",
    "strategy_summary.md": "策略报告",
    "morning_summary.md": "券商晨报",
    "final_summary.md": "综合总结",
    "contradiction_report.md": "矛盾报告",
}


class ReportsRoot:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # ── safe path resolution ──

    def _safe_dir(self, name: str) -> Path | None:
        """A directory directly under the root, by validated name."""
        if not _SEG_RE.match(name):
            return None
        p = (self.root / name).resolve()
        return p if p.is_relative_to(self.root) and p.is_dir() else None

    def _safe_file(self, run: str, rel: str) -> Path | None:
        """A file inside a run directory; rel segments are validated too."""
        if not _SEG_RE.match(run) or not rel or rel.startswith("/"):
            return None
        segments = rel.split("/")
        if not all(_SEG_RE.match(s) for s in segments):
            return None
        p = (self.root / run / rel).resolve()
        if not p.is_relative_to(self.root) or not p.is_file():
            return None
        return p

    # ── daily reports (run_report_reader.py output) ──

    def daily_dates(self) -> list[str]:
        dates = []
        for p in self.root.iterdir():
            if p.is_dir() and _DAILY_RE.match(p.name):
                dates.append(p.name)
        return sorted(dates, reverse=True)

    def daily_meta(self, day: str) -> dict:
        d = self._safe_dir(day)
        if d is None or not _DAILY_RE.match(day):
            return {}
        files = []
        for name in DAILY_FILES:
            f = d / name
            files.append({
                "name": name,
                "label": DAILY_LABELS[name],
                "exists": f.is_file(),
                "size": f.stat().st_size if f.is_file() else 0,
            })
        return {"date": day, "files": files}

    def daily_file(self, day: str, name: str) -> str | None:
        if name not in DAILY_LABELS or not _DAILY_RE.match(day):
            return None
        p = (self.root / day / name).resolve()
        if not p.is_relative_to(self.root) or not p.is_file():
            return None
        return p.read_text(encoding="utf-8", errors="replace")

    # ── trading-graph runs (reports/{TICKER}_{ts}/) ──

    def _run_dirs(self, regex: re.Pattern) -> list[Path]:
        out = []
        for p in self.root.iterdir():
            if p.is_dir() and regex.match(p.name):
                out.append(p)
        return sorted(out, key=lambda p: p.stat().st_mtime, reverse=True)

    def _run_meta(self, p: Path) -> dict:
        files = [
            str(f.relative_to(p)).replace("\\", "/")
            for f in sorted(p.rglob("*.md"))
        ]
        return {
            "id": p.name,
            "files": files,
            "mtime": p.stat().st_mtime,
        }

    def trading_runs(self) -> list[dict]:
        runs = []
        for p in self._run_dirs(_TRADING_RE):
            runs.append(self._run_meta(p))
        return runs

    def pre_runs(self) -> list[dict]:
        runs = []
        for p in self._run_dirs(_PRE_RE):
            runs.append(self._run_meta(p))
        return runs

    def run_file(self, run: str, rel: str) -> str | None:
        p = self._safe_file(run, rel)
        if p is None or not p.suffix == ".md":
            return None
        return p.read_text(encoding="utf-8", errors="replace")

    # ── recent activity (dashboard) ──

    def recent_runs(self, limit: int = 10) -> list[dict]:
        items = []
        for p in self.root.iterdir():
            if not p.is_dir():
                continue
            if _DAILY_RE.match(p.name):
                kind = "daily"
            elif _PRE_RE.match(p.name):
                kind = "pre"
            elif _TRADING_RE.match(p.name):
                kind = "trading"
            else:
                continue
            items.append({
                "id": p.name,
                "kind": kind,
                "mtime": p.stat().st_mtime,
            })
        items.sort(key=lambda x: x["mtime"], reverse=True)
        return items[:limit]

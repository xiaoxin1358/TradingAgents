"""CLI entry point for the research report reader (5 categories).

Usage:
    python run_report_reader.py
    python run_report_reader.py --date 2026-07-26
    python run_report_reader.py --smoke

Environment (used when the matching flag is omitted):
    REPORT_READER_ROOT, REPORT_READER_DATE, REPORT_READER_OUTPUT,
    REPORT_READER_DB, REPORT_READER_SMOKE=true|false
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Windows GBK console cannot print ✓/✗ from summaries; force UTF-8 so the
# final print and report-saving never crash mid-run.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure the project root is on sys.path so "tradingagents" is importable
# when this script is run directly.
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from tradingagents.agents.research_report.tools import load_all_reports  # noqa: E402
from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.research_report_graph import ResearchReportGraph  # noqa: E402
from tradingagents.llm_clients.factory import create_llm_client  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("report_reader")

DEFAULT_ROOT = r"D:\WORKS\all_data\data\report_data"
BUNDLED_SAMPLE_ROOT = _project_root / "docker" / "sample_report_data"
_TRUE = {"1", "true", "yes", "on"}

CATEGORIES = ["宏观研究", "行业研报", "个股研报", "策略报告", "券商晨报"]
CATEGORY_FIELDS = {
    "宏观研究": "macro_summary",
    "行业研报": "industry_summary",
    "个股研报": "stock_summary",
    "策略报告": "strategy_summary",
    "券商晨报": "morning_summary",
}


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUE


def _category_dirs(root: Path, date: str) -> list[str]:
    return [c for c in CATEGORIES if (root / date / c).is_dir()]


def run_smoke(root: str, date: str, output: str | None) -> int:
    """Prove the reader can start. Empty input falls back to the bundled sample. No LLM calls."""
    root_path = Path(root)
    found = _category_dirs(root_path, date) if root_path.is_dir() else []
    source = "input"
    used_root, used_date = root_path, date
    if not found:
        if not BUNDLED_SAMPLE_ROOT.is_dir():
            logger.error(
                "report reader smoke failed: no categories under %s/%s and no bundled sample at %s",
                root,
                date,
                BUNDLED_SAMPLE_ROOT,
            )
            return 1
        sample_dates = sorted(p.name for p in BUNDLED_SAMPLE_ROOT.iterdir() if p.is_dir())
        used_date = next((name for name in sample_dates if _category_dirs(BUNDLED_SAMPLE_ROOT, name)), "")
        if not used_date:
            logger.error("bundled sample has no category folders: %s", BUNDLED_SAMPLE_ROOT)
            return 1
        used_root = BUNDLED_SAMPLE_ROOT
        found = _category_dirs(used_root, used_date)
        source = "bundled-sample"
        logger.info(
            "no category folders under %s/%s; using bundled sample %s/%s",
            root,
            date,
            used_root,
            used_date,
        )

    raw = load_all_reports(str(used_root), used_date)
    loaded = sum(1 for text in raw.values() if text and not text.startswith("[ERROR]"))
    if output:
        try:
            out = Path(output)
            out.mkdir(parents=True, exist_ok=True)
            probe = out / ".smoke-ok"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            logger.error("report reader smoke cannot write output %s: %s", output, exc)
            return 1

    message = (
        f"report reader smoke OK source={source} root={used_root} "
        f"date={used_date} categories={len(found)} loaded={loaded}"
    )
    logger.info(message)
    print(message)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Research Report Reader — summarise broker research reports with LLM agents."
    )
    parser.add_argument(
        "--root",
        default=_env("REPORT_READER_ROOT") or DEFAULT_ROOT,
        help=f"Root directory of crawled report data (env REPORT_READER_ROOT, default: {DEFAULT_ROOT}).",
    )
    parser.add_argument(
        "--date",
        default=_env("REPORT_READER_DATE") or datetime.now().strftime("%Y-%m-%d"),
        help="Analysis date in YYYY-MM-DD (env REPORT_READER_DATE, default: today).",
    )
    parser.add_argument(
        "--output",
        default=_env("REPORT_READER_OUTPUT"),
        help="Output directory (env REPORT_READER_OUTPUT, default: reports/{date}/).",
    )
    parser.add_argument(
        "--db",
        default=_env("REPORT_READER_DB"),
        help="Contradictions SQLite path (env REPORT_READER_DB, default: reports/contradictions.db).",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        default=_enabled("REPORT_READER_SMOKE"),
        help="Start against empty or sample data and exit. Does not call an LLM.",
    )
    args = parser.parse_args(argv)

    if args.smoke:
        return run_smoke(args.root, args.date, args.output)

    # Validate root directory exists
    root = args.root
    if not Path(root).is_dir():
        logger.error("Root directory not found: %s", root)
        return 1

    # Validate at least one category folder exists
    existing = _category_dirs(Path(root), args.date)
    if not existing:
        logger.error("No category folders found under %s/%s/", root, args.date)
        return 1
    logger.info("Found %d category folder(s): %s", len(existing), ", ".join(existing))

    # Default output directory: reports/{date}/
    out_dir = Path(args.output) if args.output else Path("reports") / args.date
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create LLM clients
    config = dict(DEFAULT_CONFIG)
    provider = config["llm_provider"]
    backend_url = config.get("backend_url")

    logger.info("Creating LLM clients (provider=%s, quick=%s, deep=%s)...",
                provider, config["quick_think_llm"], config["deep_think_llm"])

    quick_client = create_llm_client(
        provider=provider,
        model=config["quick_think_llm"],
        base_url=backend_url,
    )
    deep_client = create_llm_client(
        provider=provider,
        model=config["deep_think_llm"],
        base_url=backend_url,
    )

    # Build & run
    db_path = args.db or str(Path("reports") / "contradictions.db")
    graph = ResearchReportGraph(
        quick_llm=quick_client.get_llm(),
        deep_llm=deep_client.get_llm(),
        db_path=db_path,
    )

    result = graph.run(report_root=root, analysis_date=args.date)

    # ── Print results ──
    for cat, field in CATEGORY_FIELDS.items():
        summary = result.get(field, "")
        if summary:
            print("\n" + "=" * 70)
            print(f"  {cat} 總結")
            print("=" * 70)
            print(summary)

    print("\n" + "=" * 70)
    print("  最終投資建議（交叉驗證）")
    print("=" * 70)
    final = result.get("final_summary", "(no advice produced)")
    print(final)

    # ── Save 6 separate reports to {out_dir}/ ──
    saved = 0
    for cat, field in CATEGORY_FIELDS.items():
        content = result.get(field, "")
        if not content:
            continue
        filename = f"{field}.md"
        filepath = out_dir / filename
        filepath.write_text(f"# {cat}總結\n\n**日期**: {args.date}\n\n{content}", encoding="utf-8")
        logger.info("Saved: %s", filepath)
        saved += 1

    if final:
        filepath = out_dir / "final_summary.md"
        filepath.write_text(f"# 綜合投資建議\n\n**日期**: {args.date}\n\n{final}", encoding="utf-8")
        logger.info("Saved: %s", filepath)
        saved += 1

    # ── Save contradiction report (v3.0, parallel branch) ──
    contradiction_report = result.get("contradiction_report", "")
    if contradiction_report:
        filepath = out_dir / "contradiction_report.md"
        filepath.write_text(contradiction_report, encoding="utf-8")
        logger.info("Saved: %s", filepath)
        saved += 1

    print(f"\nDone. {saved} report(s) saved to: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CLI entry point for the research report reader (5 categories).

Usage:
    python run_report_reader.py
    python run_report_reader.py --date 2026-07-26
"""

from __future__ import annotations

import argparse
import logging
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

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.research_report_graph import ResearchReportGraph  # noqa: E402
from tradingagents.llm_clients.factory import create_llm_client  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("report_reader")

DEFAULT_ROOT = r"D:\WORKS\all_data\data\report_data"

CATEGORIES = ["宏观研究", "行业研报", "个股研报", "策略报告", "券商晨报"]
CATEGORY_FIELDS = {
    "宏观研究": "macro_summary",
    "行业研报": "industry_summary",
    "个股研报": "stock_summary",
    "策略报告": "strategy_summary",
    "券商晨报": "morning_summary",
}


def main():
    parser = argparse.ArgumentParser(
        description="Research Report Reader — summarise broker research reports with LLM agents."
    )
    parser.add_argument(
        "--root",
        default=DEFAULT_ROOT,
        help=f"Root directory of crawled report data (default: {DEFAULT_ROOT}).",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Analysis date in YYYY-MM-DD (default: today).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: reports/{date}/).",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Path to the contradictions SQLite database (default: reports/contradictions.db).",
    )
    args = parser.parse_args()

    # Validate root directory exists
    root = args.root
    if not Path(root).is_dir():
        logger.error("Root directory not found: %s", root)
        sys.exit(1)

    # Validate at least one category folder exists
    existing = [c for c in CATEGORIES if Path(root, args.date, c).is_dir()]
    if not existing:
        logger.error("No category folders found under %s/%s/", root, args.date)
        sys.exit(1)
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


if __name__ == "__main__":
    main()

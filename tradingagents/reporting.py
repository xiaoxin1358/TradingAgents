"""Reusable report-tree writer shared by the CLI and the programmatic API.

Writes a run's per-section markdown (analysts, research, trading, risk,
portfolio) plus a consolidated ``complete_report.md`` under ``save_path``. The
CLI and ``TradingAgentsGraph.save_reports`` both call this, so a headless / API
run produces the same on-disk report tree a CLI run does.
"""

from datetime import datetime
from pathlib import Path


def write_report_tree(final_state: dict, ticker: str, save_path) -> Path:
    """Save a completed run's reports to ``save_path``; return the complete-report path."""
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    sections = []

    # 1. Analysts
    analysts_dir = save_path / "1_analysts"
    analyst_parts = []
    if final_state.get("market_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "market.md").write_text(final_state["market_report"], encoding="utf-8")
        analyst_parts.append(("Market Analyst", final_state["market_report"]))
    if final_state.get("sentiment_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "sentiment.md").write_text(final_state["sentiment_report"], encoding="utf-8")
        analyst_parts.append(("Sentiment Analyst", final_state["sentiment_report"]))
    if final_state.get("news_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "news.md").write_text(final_state["news_report"], encoding="utf-8")
        analyst_parts.append(("News Analyst", final_state["news_report"]))
    if final_state.get("fundamentals_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "fundamentals.md").write_text(final_state["fundamentals_report"], encoding="utf-8")
        analyst_parts.append(("Fundamentals Analyst", final_state["fundamentals_report"]))
    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## I. Analyst Team Reports\n\n{content}")

    # 2. Research
    if final_state.get("investment_debate_state"):
        research_dir = save_path / "2_research"
        debate = final_state["investment_debate_state"]
        research_parts = []
        if debate.get("bull_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bull.md").write_text(debate["bull_history"], encoding="utf-8")
            research_parts.append(("Bull Researcher", debate["bull_history"]))
        if debate.get("bear_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bear.md").write_text(debate["bear_history"], encoding="utf-8")
            research_parts.append(("Bear Researcher", debate["bear_history"]))
        if debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "manager.md").write_text(debate["judge_decision"], encoding="utf-8")
            research_parts.append(("Research Manager", debate["judge_decision"]))
        if research_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
            sections.append(f"## II. Research Team Decision\n\n{content}")

    # 3. Trading
    if final_state.get("trader_investment_plan"):
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(final_state["trader_investment_plan"], encoding="utf-8")
        sections.append(f"## III. Trading Team Plan\n\n### Trader\n{final_state['trader_investment_plan']}")

    # 4. Risk Management
    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risk"
        risk = final_state["risk_debate_state"]
        risk_parts = []
        if risk.get("aggressive_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "aggressive.md").write_text(risk["aggressive_history"], encoding="utf-8")
            risk_parts.append(("Aggressive Analyst", risk["aggressive_history"]))
        if risk.get("conservative_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "conservative.md").write_text(risk["conservative_history"], encoding="utf-8")
            risk_parts.append(("Conservative Analyst", risk["conservative_history"]))
        if risk.get("neutral_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "neutral.md").write_text(risk["neutral_history"], encoding="utf-8")
            risk_parts.append(("Neutral Analyst", risk["neutral_history"]))
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(f"## IV. Risk Management Team Decision\n\n{content}")

        # 5. Portfolio Manager
        if risk.get("judge_decision"):
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decision.md").write_text(risk["judge_decision"], encoding="utf-8")
            sections.append(f"## V. Portfolio Manager Decision\n\n### Portfolio Manager\n{risk['judge_decision']}")

    # Write consolidated report
    header = f"# Trading Analysis Report: {ticker}\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    (save_path / "complete_report.md").write_text(header + "\n\n".join(sections), encoding="utf-8")
    return save_path / "complete_report.md"


# ── Pre-Analyst pipeline output ──

def write_sector_report(result: dict, save_path) -> Path:
    """Save a pre-analyst pipeline result to ``save_path``.

    Writes per-analyst markdown (cyclical, growth, defensive, sector manager)
    and a consolidated ``complete_report.md``.  ``result`` is a dict with
    ``cyclical_report``, ``growth_report``, ``defensive_report``, and
    ``sector_recommendation`` keys.
    """
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)

    # Per-analyst files from dedicated report fields
    analyst_files = [
        ("cyclical_report", "cyclical_analyst.md"),
        ("growth_report", "growth_analyst.md"),
        ("defensive_report", "defensive_analyst.md"),
    ]

    for key, filename in analyst_files:
        content = result.get(key, "")
        if content:
            (save_path / filename).write_text(content, encoding="utf-8")

    # Sector Manager recommendation
    recommendation = result.get("sector_recommendation", "")
    if recommendation:
        (save_path / "sector_manager.md").write_text(recommendation, encoding="utf-8")

    # Consolidated report
    header = (
        f"# Pre-Analyst 行业分析报告\n\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    # Build consolidated: each report section then the final recommendation
    sections = []
    for key, title in (
        ("cyclical_report", "## Cyclical Analyst (宏观周期视角)"),
        ("growth_report", "## Growth Analyst (成长创新视角)"),
        ("defensive_report", "## Defensive Analyst (防御保值视角)"),
    ):
        content = result.get(key, "")
        if content:
            sections.append(f"{title}\n\n{content}")
    if recommendation:
        sections.append(f"## Sector Manager 综合建议\n\n{recommendation}")

    (save_path / "complete_report.md").write_text(
        header + "\n\n".join(sections), encoding="utf-8"
    )

    return save_path / "complete_report.md"


def _extract_speaker_section(debate_text: str, prefix: str) -> str:
    """Return the block of text from ``debate_text`` starting with ``prefix``.

    .. deprecated::
        Pre-analyst was refactored from debate to pipeline pattern (v0.3.3).
        This helper is kept for reading legacy debate-format reports but is
        no longer used by the active code path.
    """
    if not debate_text or not prefix:
        return ""

    lines = debate_text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(prefix):
            start = i
            break
    if start is None:
        return ""

    collected = []
    for line in lines[start:]:
        stripped = line.strip()
        if any(
            stripped.startswith(p)
            for p in ("Cyclical Analyst:", "Growth Analyst:", "Defensive Analyst:")
            if p != prefix
        ):
            break
        collected.append(line)

    return "\n".join(collected).strip()

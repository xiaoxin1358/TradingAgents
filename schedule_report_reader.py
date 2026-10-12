"""Keep run_report_reader.py on a cron schedule inside a container.

The default image entrypoint is still the TradingAgents CLI. This process is
the command for the compose ``report-reader`` service: it sleeps until the
next match of ``REPORT_READER_SCHEDULE`` and then runs ``run_report_reader.py``
in a child process. A failed read logs and waits for the next tick.

``--smoke`` (or ``REPORT_READER_SMOKE=true``) runs the reader's no-LLM startup
check once and exits. ``--once`` runs a real read once and exits.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger("report_reader.schedule")

ROOT = Path(__file__).resolve().parent
DEFAULT_SCHEDULE = "30 8 * * 1-5"
DEFAULT_TZ = "Asia/Shanghai"
_TRUE = {"1", "true", "yes", "on"}
_stop = False


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUE


def _schedule_expr() -> str:
    raw = os.environ.get("REPORT_READER_SCHEDULE", DEFAULT_SCHEDULE).strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        raw = raw[1:-1].strip()
    return raw or DEFAULT_SCHEDULE


def _timezone() -> ZoneInfo:
    name = os.environ.get("TZ", "").strip() or DEFAULT_TZ
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"unknown timezone {name!r}; install tzdata or set TZ to an IANA name"
        ) from exc


def _spans(field: str, minimum: int, maximum: int) -> tuple[tuple[int, int, int], ...]:
    """Parse one cron field into inclusive (start, end, step) spans."""
    spans: list[tuple[int, int, int]] = []
    for part in field.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty cron list entry in {field!r}")
        step = 1
        if "/" in part:
            range_part, step_text = part.split("/", 1)
            if not step_text.isdigit() or int(step_text) < 1:
                raise ValueError(f"invalid step in cron field {field!r}")
            step = int(step_text)
        else:
            range_part = part
        if range_part == "*":
            start, end = minimum, maximum
        else:
            if range_part == "":
                raise ValueError(f"invalid cron field {field!r}")
            if "-" in range_part:
                left, right = range_part.split("-", 1)
                try:
                    start, end = int(left), int(right)
                except ValueError as exc:
                    raise ValueError(f"invalid cron field {field!r}") from exc
            else:
                try:
                    start = end = int(range_part)
                except ValueError as exc:
                    raise ValueError(f"invalid cron field {field!r}") from exc
        if start < minimum or end > maximum or start > end:
            raise ValueError(
                f"cron field {field!r} is outside {minimum}-{maximum}"
            )
        spans.append((start, end, step))
    return tuple(spans)


def parse_cron(expr: str) -> dict:
    """Parse a 5-field cron expression (minute hour dom month dow)."""
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"cron expression must have 5 fields, got {expr!r}")
    minute, hour, dom, month, dow = fields
    return {
        "expr": expr,
        "minutes": _spans(minute, 0, 59),
        "hours": _spans(hour, 0, 23),
        "dom": _spans(dom, 1, 31),
        "months": _spans(month, 1, 12),
        "dow": _spans(dow, 0, 7),
        "dom_star": dom == "*",
        "dow_star": dow == "*",
    }


def _hit(spans: tuple[tuple[int, int, int], ...], value: int) -> bool:
    return any(start <= value <= end and (value - start) % step == 0 for start, end, step in spans)


def cron_matches(expr: str | dict, when: datetime) -> bool:
    """Return True when ``when`` matches. Day-of-month and day-of-week OR when both are set."""
    parsed = expr if isinstance(expr, dict) else parse_cron(expr)
    if not (
        _hit(parsed["minutes"], when.minute)
        and _hit(parsed["hours"], when.hour)
        and _hit(parsed["months"], when.month)
    ):
        return False
    dom_ok = _hit(parsed["dom"], when.day)
    # Cron Sunday is 0 or 7. datetime.weekday() is Monday=0 .. Sunday=6.
    cron_dow = (when.weekday() + 1) % 7
    dow_ok = _hit(parsed["dow"], cron_dow) or (cron_dow == 0 and _hit(parsed["dow"], 7))
    if parsed["dom_star"] and parsed["dow_star"]:
        return True
    if parsed["dom_star"]:
        return dow_ok
    if parsed["dow_star"]:
        return dom_ok
    return dom_ok or dow_ok


def next_run(expr: str | dict, now: datetime) -> datetime:
    """Next match strictly after ``now`` (timezone-aware)."""
    if now.tzinfo is None:
        raise ValueError("next_run requires a timezone-aware datetime")
    parsed = expr if isinstance(expr, dict) else parse_cron(expr)
    candidate = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = candidate + timedelta(days=366)
    # ponytail: minute-by-minute scan, not croniter. A DST gap/fold can skip or
    # repeat a local hour; Asia/Shanghai (the default) has no DST.
    while candidate <= limit:
        if cron_matches(parsed, candidate):
            return candidate
        candidate += timedelta(minutes=1)
    raise ValueError(f"no match for {parsed['expr']!r} within 366 days")


def run_reader(env: dict[str, str] | None = None) -> int:
    """Run run_report_reader.py. A non-zero status is returned, not raised."""
    script = ROOT / "run_report_reader.py"
    logger.info("starting %s", script.name)
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        env=env,
        check=False,
    )
    logger.info("report reader exited %s", completed.returncode)
    return int(completed.returncode)


def _on_signal(signum: int, _frame) -> None:
    global _stop
    _stop = True
    logger.info("signal %s received, stopping after the current wait", signum)


def _sleep_until(when: datetime) -> None:
    while not _stop:
        remaining = (when - datetime.now(when.tzinfo)).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 30))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Cron schedule for run_report_reader.py.")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run the reader's no-LLM startup check once and exit.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the reader once and exit (still needs data and an API key).",
    )
    args = parser.parse_args(argv)

    if args.smoke or _enabled("REPORT_READER_SMOKE"):
        env = os.environ.copy()
        env["REPORT_READER_SMOKE"] = "true"
        return run_reader(env)
    if args.once or _enabled("REPORT_READER_ONCE"):
        return run_reader()

    try:
        expr_text = _schedule_expr()
        parsed = parse_cron(expr_text)
        tz = _timezone()
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)
    logger.info("report reader scheduler started schedule=%r tz=%s", expr_text, getattr(tz, "key", tz))

    if _enabled("REPORT_READER_RUN_ON_START"):
        run_reader()

    while not _stop:
        try:
            nxt = next_run(parsed, datetime.now(tz))
        except ValueError as exc:
            logger.error("%s", exc)
            return 1
        logger.info("next report reader run at %s", nxt.isoformat())
        _sleep_until(nxt)
        if _stop:
            break
        run_reader()

    logger.info("report reader scheduler stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())

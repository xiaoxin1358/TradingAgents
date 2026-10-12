"""Cron matching and report-reader smoke. No LLM calls and no Spider data."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import run_report_reader
from schedule_report_reader import (
    DEFAULT_SCHEDULE,
    DEFAULT_TZ,
    cron_matches,
    main,
    next_run,
    parse_cron,
)

TZ = ZoneInfo("Asia/Shanghai")
SCHEDULE = DEFAULT_SCHEDULE


def test_compose_defaults_match_scheduler():
    text = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert f"REPORT_READER_SCHEDULE:-{DEFAULT_SCHEDULE}" in text
    assert f"REPORT_READER_TZ:-{DEFAULT_TZ}" in text


def test_weekday_morning_matches_and_weekend_does_not():
    monday = datetime(2026, 10, 12, 8, 30, tzinfo=TZ)
    assert cron_matches(SCHEDULE, monday)
    assert not cron_matches(SCHEDULE, monday.replace(minute=31))
    sunday = datetime(2026, 10, 11, 8, 30, tzinfo=TZ)
    assert not cron_matches(SCHEDULE, sunday)
    assert cron_matches("30 8 * * 0", sunday)
    assert cron_matches("30 8 * * 7", sunday)


def test_next_run_skips_weekend_and_the_current_slot():
    at_slot = datetime(2026, 10, 12, 8, 30, tzinfo=TZ)
    assert next_run(SCHEDULE, at_slot) == datetime(2026, 10, 13, 8, 30, tzinfo=TZ)
    friday_after = datetime(2026, 10, 16, 9, 0, tzinfo=TZ)
    assert next_run(SCHEDULE, friday_after) == datetime(2026, 10, 19, 8, 30, tzinfo=TZ)


def test_dom_and_dow_match_either_day():
    expr = "0 0 1 * 1"
    assert cron_matches(expr, datetime(2026, 10, 12, 0, 0, tzinfo=TZ))
    assert cron_matches(expr, datetime(2026, 10, 1, 0, 0, tzinfo=TZ))
    assert not cron_matches(expr, datetime(2026, 10, 2, 0, 0, tzinfo=TZ))


def test_step_and_reject_bad_expr():
    assert cron_matches("0 */6 * * *", datetime(2026, 10, 12, 18, 0, tzinfo=TZ))
    assert not cron_matches("0 */6 * * *", datetime(2026, 10, 12, 7, 0, tzinfo=TZ))
    with pytest.raises(ValueError):
        parse_cron("30 8 * *")
    with pytest.raises(ValueError):
        parse_cron("30 8 * * MON")
    with pytest.raises(ValueError):
        next_run(SCHEDULE, datetime(2026, 10, 12, 8, 30))


def test_smoke_empty_root_uses_bundled_sample(tmp_path, capsys):
    rc = run_report_reader.main(
        ["--smoke", "--root", str(tmp_path / "empty"), "--output", str(tmp_path / "out")]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "report reader smoke OK" in out
    assert "source=bundled-sample" in out
    assert "date=2026-01-01" in out
    assert "categories=5" in out
    assert "loaded=5" in out
    assert not (tmp_path / "out" / ".smoke-ok").exists()
    assert (tmp_path / "out").is_dir()


def test_smoke_empty_category_dirs(tmp_path, capsys):
    day = "2026-10-12"
    root = tmp_path / "root"
    for cat in run_report_reader.CATEGORIES:
        (root / day / cat).mkdir(parents=True)
    rc = run_report_reader.main(
        ["--smoke", "--root", str(root), "--date", day, "--output", str(tmp_path / "out")]
    )
    assert rc == 0
    assert "source=input" in capsys.readouterr().out


def test_smoke_env_does_not_call_llm(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORT_READER_SMOKE", "true")

    def boom(*_args, **_kwargs):
        raise AssertionError("LLM client should not be created")

    monkeypatch.setattr(run_report_reader, "create_llm_client", boom)
    rc = run_report_reader.main(
        ["--root", str(tmp_path / "missing"), "--output", str(tmp_path / "out")]
    )
    assert rc == 0


def test_missing_data_exits_before_llm(tmp_path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("LLM client should not be created")

    monkeypatch.setattr(run_report_reader, "create_llm_client", boom)
    assert run_report_reader.main(["--root", str(tmp_path / "missing"), "--date", "2026-10-12"]) == 1
    root = tmp_path / "root"
    root.mkdir()
    assert run_report_reader.main(["--root", str(root), "--date", "2026-10-12"]) == 1


def test_scheduler_smoke_and_bad_schedule(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORT_READER_ROOT", str(tmp_path / "missing"))
    monkeypatch.setenv("REPORT_READER_OUTPUT", str(tmp_path / "out"))
    assert main(["--smoke"]) == 0
    monkeypatch.setenv("REPORT_READER_SCHEDULE", "not a cron")
    assert main([]) == 1


def test_scheduler_once_missing_root_exits(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORT_READER_ROOT", str(tmp_path / "missing"))
    monkeypatch.delenv("REPORT_READER_SMOKE", raising=False)
    assert main(["--once"]) == 1

"""M2 job-runner unit checks with stand-in commands (never runs the real
graphs) — docs/vue-frontend.md §12.7."""

import json
import sys
import time
from pathlib import Path

import pytest

from webapi import jobs as jobs_mod
from webapi.jobs import JobError, JobManager, validate_params


def _standin_cmd(code: str, pause: float = 0.2) -> list[str]:
    return [sys.executable, "-c", f"import time; {code}; time.sleep({pause})"]


@pytest.fixture()
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(
        jobs_mod,
        "_command",
        lambda job_type, params: _standin_cmd("print('t1'); print('t2'); print('t3')"),
    )
    return JobManager(tmp_path)


def test_validate_rejects_bad_params():
    with pytest.raises(JobError):
        validate_params("daily", {"date": "2026-13-40"})
    with pytest.raises(JobError):
        validate_params("daily", {"date": "../../etc"})
    with pytest.raises(JobError):
        validate_params("pre", {"ticker": "A;B"})
    with pytest.raises(JobError):
        validate_params("trading", {})
    assert validate_params("daily", {"date": "2026-08-13"}) == {"date": "2026-08-13"}
    assert validate_params("pre", {"ticker": "SPY", "date": "2026-08-13"}) == {
        "ticker": "SPY", "date": "2026-08-13",
    }


def test_spider_validate_and_command():
    # defaults
    assert validate_params("spider", {}) == {"report_type": "industry"}
    # invalid report type / date range / limit
    with pytest.raises(JobError):
        validate_params("spider", {"report_type": "xxx"})
    with pytest.raises(JobError):
        validate_params("spider", {"report_type": "macro", "start": "2026-08-15", "end": "2026-08-10"})
    with pytest.raises(JobError):
        validate_params("spider", {"report_type": "macro", "test": True, "limit": "abc"})
    with pytest.raises(JobError):
        validate_params("spider", {"report_type": "macro", "test": True, "limit": 999})
    # full valid params
    v = validate_params("spider", {
        "report_type": "macro", "test": True, "limit": 3,
        "start": "2026-08-10", "end": "2026-08-15",
    })
    assert v == {
        "report_type": "macro", "start": "2026-08-10",
        "end": "2026-08-15", "test": True, "limit": "3",
    }
    # command mapping
    cmd = jobs_mod._command("spider", v)
    assert cmd[:2] == [sys.executable, "-m"]
    assert "src.industry_report_spider.industry_report_spider" in cmd
    assert "--type" in cmd and "macro" in cmd
    assert "--start" in cmd and "--end" in cmd and "--test" in cmd and "--limit" in cmd
    # cwd points at the spider repo, not the project root
    assert jobs_mod._cwd("spider").name == "all_data"
    assert jobs_mod._cwd("daily") != jobs_mod._cwd("spider")


def test_job_runs_to_done_and_persists(manager):
    job = manager.start("daily", {"date": "2026-08-13"})
    for _ in range(50):
        if manager.get(job["id"])["status"] != "running":
            break
        time.sleep(0.1)
    done = manager.get(job["id"])
    assert done["status"] == "done" and done["exit_code"] == 0
    assert done["finished_at"] is not None
    # jobs.json persisted on disk
    saved = json.loads((manager.jobs_dir / "jobs.json").read_text(encoding="utf-8"))
    assert saved[job["id"]]["status"] == "done"


def test_log_file_written(manager):
    job = manager.start("daily", {"date": "2026-08-13"})
    for _ in range(50):
        if manager.get(job["id"])["status"] != "running":
            break
        time.sleep(0.1)
    tail = manager.log_tail(job["id"])
    assert "t1" in tail and "t3" in tail


def test_single_job_lock(manager, monkeypatch):
    monkeypatch.setattr(
        jobs_mod,
        "_command",
        lambda job_type, params: _standin_cmd("print('slow')", pause=2.0),
    )
    manager.start("pre", {"ticker": "SPY"})
    with pytest.raises(JobError) as exc:
        manager.start("pre", {"ticker": "SPY"})
    assert exc.value.status == 409
    manager.shutdown()


def test_restore_marks_running_as_interrupted(tmp_path):
    base = tmp_path
    (base / "jobs.json").write_text(
        json.dumps({
            "abc123": {
                "id": "abc123", "type": "daily",
                "params": {"date": "2026-08-13"}, "status": "running",
                "pid": 999999, "created_at": 0, "finished_at": None,
                "exit_code": None, "log_file": "jobs/abc123.log",
            }
        }),
        encoding="utf-8",
    )
    mgr = JobManager(base)
    assert mgr.get("abc123")["status"] == "interrupted"

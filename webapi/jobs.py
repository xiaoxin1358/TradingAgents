"""M2 job runner: whitelisted subprocess tasks + SSE log streaming.

docs/vue-frontend.md §12. Deliberate simplifications (ponytail:):
- global single-job lock — fine for one user; upgrade path: per-user jobs + queue
- restart recovery only re-labels running jobs as interrupted and tries
  taskkill on the recorded pid — a surviving orphan that already detached
  is left to finish on its own (its reports still land on disk)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import re
import secrets
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TICKER_RE = re.compile(r"^[A-Za-z0-9._-]{1,20}$")
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_JOBS_DIR = Path(os.environ.get(
    "TRADINGAGENTS_WEB_JOBS_DIR",
    Path.home() / ".tradingagents",  # jobs.json 在此目录，日志在 jobs/ 子目录
))


class JobError(Exception):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


def _is_valid_date(s: str) -> bool:
    if not _DATE_RE.match(s or ""):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def validate_params(job_type: str, params: dict) -> dict:
    """Whitelist the params per task type; raise JobError on anything else."""
    if job_type not in ("daily", "pre"):
        raise JobError(f"任务类型暂不支持: {job_type}")
    out: dict = {}
    if job_type == "daily":
        date = params.get("date")
        if not _is_valid_date(date):
            raise JobError("日期格式非法,应为 YYYY-MM-DD")
        out["date"] = date
        root = params.get("root")
        if root:
            allowed = os.environ.get("TRADINGAGENTS_REPORT_ROOT")
            if not allowed or root != allowed:
                raise JobError("数据根目录不在后端白名单内")
            out["root"] = root
    else:  # pre
        ticker = (params.get("ticker") or "").strip() or "SPY"
        if not _TICKER_RE.match(ticker):
            raise JobError("标的格式非法")
        out["ticker"] = ticker
        date = params.get("date")
        if date:
            if not _is_valid_date(date):
                raise JobError("日期格式非法,应为 YYYY-MM-DD")
            out["date"] = date
    return out


def _command(job_type: str, params: dict) -> list[str]:
    """Whitelisted argv per task type — always shell=False (docs 12.3)."""
    if job_type == "daily":
        cmd = [sys.executable, "run_report_reader.py", "--date", params["date"]]
        if params.get("root"):
            cmd += ["--root", params["root"]]
        return cmd
    cmd = [sys.executable, "run_pre_analyst.py", "--ticker", params["ticker"]]
    if params.get("date"):
        cmd += ["--date", params["date"]]
    return cmd


class JobManager:
    def __init__(self, jobs_dir: Path | str = _JOBS_DIR):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.jobs_dir / "jobs.json"
        self._lock = threading.Lock()
        self.jobs: dict[str, dict] = {}
        self._procs: dict[str, subprocess.Popen] = {}
        self._queues: dict[str, queue.Queue] = {}
        self._load()
        self._restore()

    # ── persistence ──

    def _load(self) -> None:
        if self._path.is_file():
            try:
                self.jobs = json.loads(self._path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                self.jobs = {}

    def _save(self) -> None:
        # atomic write: tmp + os.replace, never a torn ledger (docs 12.2)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.jobs, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        os.replace(tmp, self._path)

    def _restore(self) -> None:
        """Backend restarted: running jobs whose subprocess is gone become
        interrupted instead of running forever (docs 12.3)."""
        changed = False
        for job in self.jobs.values():
            if job.get("status") != "running":
                continue
            pid = job.get("pid")
            if pid:
                try:
                    # still alive? kill it and mark interrupted
                    check = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
                        capture_output=True, text=True, timeout=10,
                    )
                    if str(pid) in check.stdout:
                        subprocess.run(
                            ["taskkill", "/PID", str(pid), "/F"],
                            capture_output=True, timeout=10,
                        )
                except (OSError, subprocess.TimeoutExpired):
                    pass
            job["status"] = "interrupted"
            job["finished_at"] = job.get("finished_at") or int(_now())
            changed = True
        if changed:
            self._save()

    # ── job lifecycle ──

    def start(self, job_type: str, params: dict) -> dict:
        params = validate_params(job_type, params)
        with self._lock:
            if any(j.get("status") == "running" for j in self.jobs.values()):
                raise JobError("已有任务在运行", status=409)
            job_id = secrets.token_hex(3)
            log_file = f"jobs/{job_id}.log"
            job = {
                "id": job_id,
                "type": job_type,
                "params": params,
                "status": "running",
                "pid": None,
                "created_at": int(_now()),
                "finished_at": None,
                "exit_code": None,
                "log_file": log_file,
            }
            self.jobs[job_id] = job
            self._save()

        log_path = self.jobs_dir / "jobs" / f"{job_id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        q: queue.Queue = queue.Queue()
        self._queues[job_id] = q
        try:
            proc = subprocess.Popen(
                _command(job_type, params),
                cwd=_PROJECT_ROOT,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8",
                     "PYTHONUNBUFFERED": "1"},
            )
        except OSError as exc:
            job["status"] = "failed"
            job["finished_at"] = int(_now())
            job["exit_code"] = -1
            with self._lock:
                self._save()
            q.put(("log", f"[webapi] 无法启动子进程: {exc}"))
            q.put(("status", job))
            return job

        job["pid"] = proc.pid
        with self._lock:
            self._save()
        self._procs[job_id] = proc
        threading.Thread(
            target=self._pump, args=(job_id, proc, log_path, q), daemon=True
        ).start()
        return job

    def _pump(self, job_id: str, proc: subprocess.Popen, log_path: Path,
              q: queue.Queue) -> None:
        """Read child stdout line by line: append to log file, broadcast."""
        with open(log_path, "a", encoding="utf-8") as fh:
            assert proc.stdout is not None
            for line in proc.stdout:
                line = _ANSI_RE.sub("", line).rstrip("\r\n")
                fh.write(line + "\n")
                fh.flush()
                q.put(("log", line))
        exit_code = proc.wait()
        job = self.jobs[job_id]
        with self._lock:
            job["status"] = "done" if exit_code == 0 else "failed"
            job["exit_code"] = exit_code
            job["finished_at"] = int(_now())
            self._save()
        q.put(("status", job))
        self._procs.pop(job_id, None)

    def cancel(self, job_id: str) -> dict | None:
        job = self.jobs.get(job_id)
        if job is None:
            return None
        if job.get("status") == "running":
            proc = self._procs.get(job_id)
            if proc is not None:
                proc.kill()  # Windows: TerminateProcess, single-process jobs only
        with self._lock:
            if job.get("status") == "running":
                job["status"] = "cancelled"
                job["finished_at"] = int(_now())
                self._save()
        if job_id in self._queues:
            self._queues[job_id].put(("status", job))
        return job

    def shutdown(self) -> None:
        """FastAPI lifespan exit: kill the running child (docs 12.3)."""
        for job_id, proc in self._procs.items():
            try:
                proc.kill()
            except OSError:
                pass
            job = self.jobs.get(job_id)
            if job and job.get("status") == "running":
                job["status"] = "interrupted"
                job["finished_at"] = int(_now())
        with self._lock:
            self._save()

    # ── reads ──

    def list(self) -> list[dict]:
        return sorted(self.jobs.values(),
                      key=lambda j: j.get("created_at", 0), reverse=True)

    def get(self, job_id: str) -> dict | None:
        return self.jobs.get(job_id)

    def log_tail(self, job_id: str, limit: int = 500) -> list[str]:
        job = self.jobs.get(job_id)
        if not job:
            return []
        log_path = self.jobs_dir / job["log_file"]
        if not log_path.is_file():
            return []
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-limit:]

    # ── SSE ──

    async def events(self, job_id: str):
        """Replay the log file, then stream new lines; never blocks the loop
        (poll queue with get_nowait, docs 12.3)."""
        job = self.jobs.get(job_id)
        if job is None:
            yield "event: status\ndata: {\"error\": \"not found\"}\n\n"
            return
        for line in self.log_tail(job_id):
            yield f"event: log\ndata: {json.dumps({'line': line}, ensure_ascii=False)}\n\n"
        q = self._queues.get(job_id)
        idle = 0
        while True:
            status = job.get("status")
            if status != "running":
                yield f"event: status\ndata: {json.dumps(job, ensure_ascii=False)}\n\n"
                return
            if q is not None:
                try:
                    kind, payload = q.get_nowait()
                    if kind == "log":
                        yield f"event: log\ndata: {json.dumps({'line': payload}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"event: status\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    idle = 0
                    continue
                except queue.Empty:
                    pass
            idle += 1
            if idle % 30 == 0:  # keep-alive every ~15s
                yield ": ping\n\n"
            await asyncio.sleep(0.5)


def _now() -> float:
    return datetime.now().timestamp()

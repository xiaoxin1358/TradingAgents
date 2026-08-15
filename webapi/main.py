"""FastAPI entry for the TradingAgents web UI (docs/vue-frontend.md, M1).

Run:
    python -m uvicorn webapi.main:app --port 8000

Only reads reports/ + contradictions.db; never imports the tradingagents
package or any LLM client. M2 job control lives in a later milestone.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import contradictions as ctr
from . import jobs as jobs_mod
from . import reports as rpt
from . import settings as stg

_ROOT = Path(__file__).resolve().parent.parent
_REPORTS_DIR = Path(os.environ.get("TRADINGAGENTS_REPORTS_DIR", _ROOT / "reports"))
_DB_PATH = _REPORTS_DIR / "contradictions.db"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    jobs.shutdown()  # kill running child on backend exit (docs 12.3)


app = FastAPI(title="TradingAgents Web API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

root = rpt.ReportsRoot(_REPORTS_DIR)
jobs = jobs_mod.JobManager()


# ── overview / dashboard ──────────────────────────────────────────────

@app.get("/api/overview")
def overview():
    cstats = ctr.stats(_DB_PATH)
    recent = root.recent_runs(10)
    top = ctr.list_contradictions(_DB_PATH, status="open", limit=5)["rows"]
    top5 = [
        {
            "id": r["id"],
            "subject": r["subject"],
            "direction_a": r["direction_a"],
            "direction_b": r["direction_b"],
            "broker_a": r["claim_a"].get("broker", "?"),
            "broker_b": r["claim_b"].get("broker", "?"),
            "days_open": r["days_open"],
            "cause_type": (r["insight"] or {}).get("cause_type", "未生成"),
        }
        for r in top
    ]
    return {
        "stats": {
            "daily_days": len(root.daily_dates()),
            "trading_runs": len(root.trading_runs()),
            "contradictions": cstats,
        },
        "recent": recent,
        "top5": top5,
    }


# ── daily research reports ────────────────────────────────────────────

@app.get("/api/dates")
def dates():
    return {"dates": root.daily_dates()}


@app.get("/api/reports/{day}")
def report_meta(day: str):
    meta = root.daily_meta(day)
    if not meta:
        raise HTTPException(404, "no reports for this date")
    return meta


@app.get("/api/reports/{day}/{name}")
def report_file(day: str, name: str):
    content = root.daily_file(day, name)
    if content is None:
        raise HTTPException(404, "report not found")
    return {"name": name, "content": content}


# ── trading-graph / pre-analyst runs ──────────────────────────────────

@app.get("/api/trading-runs")
def trading_runs():
    return {"runs": root.trading_runs()}


@app.get("/api/trading-runs/{run}/{path:path}")
def trading_file(run: str, path: str):
    content = root.run_file(run, path)
    if content is None:
        raise HTTPException(404, "file not found")
    return {"path": path, "content": content}


@app.get("/api/pre-runs")
def pre_runs():
    return {"runs": root.pre_runs()}


@app.get("/api/pre-runs/{run}/{path:path}")
def pre_file(run: str, path: str):
    content = root.run_file(run, path)
    if content is None:
        raise HTTPException(404, "file not found")
    return {"path": path, "content": content}


# ── contradictions (v3.3) ─────────────────────────────────────────────

@app.get("/api/contradictions")
def contradiction_list(
    status: str | None = Query(None, pattern=r"^(open|resolved)$"),
    kind: str | None = Query(None, pattern=r"^(factual|opinion)$"),
    scope: str | None = Query(None, pattern=r"^(direct|indirect)$"),
    scale: str | None = Query(None, pattern=r"^(same|cross)$"),
    subject: str | None = Query(None, max_length=64),
    cause_type: str | None = Query(None, max_length=32),
    min_days: int | None = Query(None, ge=0, le=3650),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return ctr.list_contradictions(
        _DB_PATH,
        status=status, kind=kind, scope=scope, scale=scale,
        subject=subject, cause_type=cause_type, min_days=min_days,
        limit=limit, offset=offset,
    )


@app.get("/api/contradictions/stats")
def contradiction_stats():
    return ctr.stats(_DB_PATH)


@app.get("/api/contradictions/{cid}")
def contradiction_detail(cid: str):
    row = ctr.get_contradiction(_DB_PATH, cid)
    if row is None:
        raise HTTPException(404, "contradiction not found")
    return row


# ── memory / settings ─────────────────────────────────────────────────

@app.get("/api/memory")
def memory():
    return stg.get_memory(_ROOT)


# ── jobs (M2, docs 12) ───────────────────────────────────────────────

@app.post("/api/jobs", status_code=201)
def create_job(payload: dict = Body(...)):
    job_type = payload.get("type")
    params = payload.get("params") or {}
    if not isinstance(job_type, str) or not isinstance(params, dict):
        raise HTTPException(422, "body 应为 {type, params}")
    try:
        return jobs.start(job_type, params)
    except jobs_mod.JobError as exc:
        raise HTTPException(exc.status, str(exc))


@app.get("/api/jobs")
def list_jobs():
    return {"jobs": jobs.list()}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return {**job, "log_tail": jobs.log_tail(job_id)}


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = jobs.cancel(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    return job


@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str):
    if jobs.get(job_id) is None:
        raise HTTPException(404, "job not found")
    return StreamingResponse(
        jobs.events(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/settings")
def settings():
    return stg.get_settings(_ROOT)

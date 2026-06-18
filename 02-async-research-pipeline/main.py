"""
Async research pipeline — POST job, poll GET, no Redis, no Celery.
Run: pip install -r requirements.txt && uvicorn main:app --reload
"""
import os, uuid, asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI

MINIMAX_KEY = os.environ["MINIMAX_API_KEY"]
BASE_URL    = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")
STATE_DIR   = Path("state/jobs")
STATE_DIR.mkdir(parents=True, exist_ok=True)

app      = app = FastAPI(title="Async Research Pipeline")
client   = AsyncOpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)


class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"   # standard | deep


class JobState(BaseModel):
    id: str
    status: str                # queued | running | done | failed
    topic: str
    created_at: str
    result: Optional[str] = None
    error: Optional[str] = None


def _path(job_id: str) -> Path:
    return STATE_DIR / f"{job_id}.json"

def _load(job_id: str) -> JobState:
    p = _path(job_id)
    if not p.exists():
        raise HTTPException(404, f"job {job_id} not found")
    return JobState(**json.loads(p.read_text()))

def _save(job: JobState):
    _path(job.id).write_text(job.model_dump_json())


async def _run_research(job: JobState, depth: str):
    job.status = "running"
    _save(job)

    try:
        system = (
            "You are a research analyst. Given a topic, produce a structured report with: "
            "1) Executive summary (3 sentences) "
            "2) Key findings (5 bullet points) "
            "3) Recommended next steps (3 actions) "
            "Be concise and actionable."
        )
        user = f"Research topic: {job.topic}"
        if depth == "deep":
            user += "\n\nGo deep: include market sizing, key players, and risk factors."

        response = await client.chat.completions.create(
            model="MiniMax-M3",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        job.result = response.choices[0].message.content
        job.status = "done"

    except Exception as e:
        job.error  = str(e)
        job.status = "failed"

    _save(job)


@app.post("/research", response_model=JobState, status_code=202)
async def submit(req: ResearchRequest, bg: BackgroundTasks):
    job = JobState(
        id=str(uuid.uuid4())[:8],
        status="queued",
        topic=req.topic,
        created_at=datetime.utcnow().isoformat(),
    )
    _save(job)
    bg.add_task(_run_research, job, req.depth)
    return job


@app.get("/research/{job_id}", response_model=JobState)
async def get_job(job_id: str):
    return _load(job_id)


@app.get("/research")
async def list_jobs():
    jobs = [JobState(**json.loads(p.read_text())) for p in STATE_DIR.glob("*.json")]
    return sorted(jobs, key=lambda j: j.created_at, reverse=True)


@app.get("/health")
async def health():
    return {"status": "ok"}

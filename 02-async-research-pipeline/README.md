# 02 — Async Research Pipeline

A FastAPI service that accepts research jobs asynchronously — no Redis, no Celery, no message broker. State persisted as JSON files.

## What it does

- `POST /research` → returns `job_id` immediately (202 Accepted)
- `GET /research/{job_id}` → poll for status/result
- `GET /research` → list all jobs
- Background task runs MiniMax M3 and writes result to disk

## Setup

```bash
pip install -r requirements.txt

export MINIMAX_API_KEY=your_key
uvicorn main:app --reload
```

## Usage

```bash
# Submit a job
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI agent frameworks in 2025", "depth": "standard"}'
# → {"id": "a3f2c1b0", "status": "queued", ...}

# Poll until done
curl http://localhost:8000/research/a3f2c1b0
# → {"status": "done", "result": "..."}
```

## Why no Redis?

For workloads under ~1000 concurrent jobs, file-based state is simpler, cheaper, and easier to debug. You can `cat state/jobs/*.json` to inspect every job. Add Redis when you actually need it.

## Extend it

- Add authentication: `x-api-key` header check in a FastAPI dependency
- Add webhooks: store a `callback_url` in the request, POST to it when done
- Add retries: catch specific errors and re-queue with exponential backoff
- Add multiple workers: replace `BackgroundTasks` with `asyncio.Queue` + worker pool

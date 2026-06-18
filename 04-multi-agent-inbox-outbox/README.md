# 04 — Multi-Agent Inbox/Outbox

Builder + Reviewer pattern via file-based message bus. No message broker, no database — just directories and JSON files.

## What it does

1. Submit a task → lands in `bus/inbox/builder/`
2. Builder agent implements it → result moves to `bus/inbox/reviewer/`
3. Reviewer scores and verdicts → final result in `bus/outbox/`
4. If `needs_revision` → re-queued with feedback for next round (up to 3)

## Setup

```bash
pip install -r requirements.txt
export MINIMAX_API_KEY=your_key
python run.py "build a FastAPI endpoint that returns the current UTC time"
```

## Output

```
Submitted: a3f2c1b0
Task: build a FastAPI endpoint that returns the current UTC time

--- Round 1 ---
[builder] working on: build a FastAPI endpoint...
[builder] done, sent to reviewer
[reviewer] reviewing: build a FastAPI endpoint...
[reviewer] verdict: passed (score 9)

PASSED in 1 round(s)
=== Code ===
from fastapi import FastAPI
from datetime import datetime, timezone
app = FastAPI()

@app.get("/time")
def current_time():
    return {"utc": datetime.now(timezone.utc).isoformat()}
```

## Why file-based bus

- Every packet is readable with `cat bus/outbox/*.json`
- Debugging is `ls` + `cat`, not a queue dashboard
- Survives process restarts without losing work
- Trivially portable to Redis/RabbitMQ later if needed

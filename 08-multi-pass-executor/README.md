# 08 — Multi-Pass Executor

An LLM state machine that splits any task into three sequential phases: understand → plan → execute. Each phase persists to disk, so the process can be interrupted and resumed without repeating work.

## Setup

```bash
pip install -r requirements.txt
export MINIMAX_API_KEY=your_key
python main.py "build a CLI password generator in Python"
```

## Usage

```
[UNDERSTAND] Running...
[UNDERSTAND] done in 3.2s
------------------------------------------------------------
Task: build a CLI password generator in Python
What must be built: A command-line tool that generates secure passwords...
Constraints: Pure Python stdlib, no external deps, cross-platform...
Ambiguities: Password length default? Character set options?

[PLAN] Running...
[PLAN] done in 4.1s
------------------------------------------------------------
1. Parse CLI args: --length (default 16), --no-symbols, --count
2. Build character pool from string.ascii_letters + digits + punctuation
3. Use secrets.choice() for cryptographic randomness
...

[EXECUTE] Running...
[EXECUTE] done in 5.8s
------------------------------------------------------------
import argparse, secrets, string
...

[DONE] All phases complete. State saved to state.json
```

Resume after interruption:
```bash
python main.py   # no args — auto-resumes from state.json
```

## How it works

```
task description
      |
  [UNDERSTAND]  ─── identifies what/constraints/ambiguities
      |
   [PLAN]       ─── numbered, concrete steps
      |
  [EXECUTE]     ─── final deliverable (code / config / doc)
      |
  state.json    ─── persists each phase; skip if already done
```

Each phase builds on the previous: the executor has full context of understanding + plan, preventing the LLM from taking shortcuts or drifting from the original intent.

## Extend it

**Add a review phase**: After execute, add a `review` phase that reads the output and checks it against the plan.

**Parallelise exploration**: In the plan phase, fan out to N sub-agents, each exploring a different approach, then merge the best plan.

**Integrate with the agent factory**: Wrap this as a packet type and drop it into the inbox/outbox pattern from recipe 04.

# AI Agent Cookbook

Runnable recipes for building AI agents with [MiniMax M3](https://www.minimaxi.com/) — the flat-rate LLM that makes production agents economically viable.

Each recipe is self-contained: clone, set one env var, run.

## Recipes

| # | Recipe | What you get |
|---|---|---|
| 01 | [Discord Bot with Tools](01-discord-bot-with-tools/) | Bot that runs bash, reads files, searches the web |
| 02 | [Async Research Pipeline](02-async-research-pipeline/) | POST job → poll GET, no Redis, no Celery |
| 03 | [Demand Scraper + Classifier](03-demand-scraper-classifier/) | Multi-source scraper with AI scoring |
| 04 | [Multi-Agent Inbox/Outbox](04-multi-agent-inbox-outbox/) | Two agents collaborating via file-based bus |
| 05 | [Persistent Memory Agent](05-persistent-memory-agent/) | FTS5 SQLite recall + daily digest |
| 06 | [PDF Q&A Bot](06-pdf-qa-bot/) | Upload PDF → ask questions |
| 07 | [Voice Discord Bot](07-voice-discord-bot/) | Whisper STT → MiniMax → TTS reply |
| 08 | [Multi-Pass Executor](08-multi-pass-executor/) | understand → plan → execute with persisted state |

## Setup

All recipes use the same env var:

```bash
export MINIMAX_API_KEY=your_key_here
export MINIMAX_BASE_URL=https://api.minimax.io/anthropic/v1
```

MiniMax offers an [Anthropic-compatible API](https://www.minimaxi.com/) — most recipes also work with `ANTHROPIC_API_KEY` by swapping the base URL.

## Why MiniMax M3

- Flat-rate pricing — no per-token billing surprises in production
- Anthropic-compatible API — swap from Claude with one env var change
- Multimodal — text, vision, audio in one model
- Fast enough for Discord bots (<2s typical response)

## Philosophy

Every recipe is:
- **Self-contained** — one folder, one `requirements.txt`, one `README.md`
- **Runnable in under 5 minutes** — no Docker required for basics
- **Production-extracted** — patterns from real running agents, not toy examples
- **Under 200 lines** — readable in one sitting

---

Built by [Hélio Gil](https://github.com/heliogil) — AI venture builder.

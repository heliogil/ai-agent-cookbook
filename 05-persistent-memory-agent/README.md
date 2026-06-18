# 05 — Persistent Memory Agent

Conversational agent that remembers everything via FTS5 SQLite. No vector database, no embeddings — just full-text search. Generates a daily digest on demand.

## What it does

- Every message (user + assistant) stored in SQLite FTS5
- Before each reply, recalls relevant past messages via full-text search
- `digest` command → summarises today's conversation in 3 bullets
- Zero external dependencies beyond `openai`

## Setup

```bash
pip install -r requirements.txt
export MINIMAX_API_KEY=your_key
python agent.py
```

## Usage

```
You: My name is Hélio and I'm building a PC comparator for Brazil
Agent: Nice to meet you, Hélio! A PC comparator for Brazil sounds like...

You: What was the project I mentioned?
Agent: You mentioned building a PC comparator for Brazil...  ← recalled from memory

You: digest
Today's digest:
• Hélio introduced himself and mentioned a PC hardware comparator project for Brazil
• Discussed the Brazilian market opportunity for cost/performance comparisons
• ...
```

## Why FTS5 instead of embeddings

- Zero cost — no embedding API calls
- Instant — SQLite query in <10ms
- Debuggable — `sqlite3 memory.db "SELECT * FROM messages"` shows everything
- Good enough for most recall tasks (keyword overlap catches ~85% of relevant context)

Add vector search (pgvector, ChromaDB) when you need semantic similarity across thousands of long documents.

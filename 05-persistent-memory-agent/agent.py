"""
Persistent memory agent — FTS5 SQLite recall + daily digest.
Every message is stored and recalled via full-text search.
Run: pip install -r requirements.txt && python agent.py
"""
import os, sqlite3, hashlib
from datetime import datetime, date
from pathlib import Path
from openai import OpenAI

MINIMAX_KEY = os.environ["MINIMAX_API_KEY"]
BASE_URL    = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")
DB_PATH     = Path("memory.db")

ai = OpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)


# ── Database ───────────────────────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE VIRTUAL TABLE IF NOT EXISTS messages USING fts5(
            role, content, ts, tokenize='porter ascii'
        );
        CREATE TABLE IF NOT EXISTS digests (
            day TEXT PRIMARY KEY,
            summary TEXT,
            created_at TEXT
        );
    """)
    con.commit()
    return con


def store(con: sqlite3.Connection, role: str, content: str):
    con.execute("INSERT INTO messages VALUES (?, ?, ?)",
                (role, content, datetime.utcnow().isoformat()))
    con.commit()


def recall(con: sqlite3.Connection, query: str, limit: int = 5) -> list[dict]:
    rows = con.execute(
        "SELECT role, content, ts FROM messages WHERE messages MATCH ? "
        "ORDER BY rank LIMIT ?", (query, limit)
    ).fetchall()
    return [{"role": r, "content": c, "ts": t} for r, c, t in rows]


def get_or_create_digest(con: sqlite3.Connection, today: str) -> str:
    row = con.execute("SELECT summary FROM digests WHERE day=?", (today,)).fetchone()
    if row:
        return row[0]

    rows = con.execute(
        "SELECT role, content FROM messages WHERE ts LIKE ? ORDER BY ts",
        (f"{today}%",)
    ).fetchall()
    if not rows:
        return "(no messages today yet)"

    history = "\n".join(f"{r}: {c}" for r, c in rows)
    resp = ai.chat.completions.create(
        model="MiniMax-M3",
        messages=[
            {"role": "system", "content": "Summarise this conversation in 3 bullet points. Be concise."},
            {"role": "user",   "content": history},
        ],
    )
    summary = resp.choices[0].message.content
    con.execute("INSERT OR REPLACE INTO digests VALUES (?, ?, ?)",
                (today, summary, datetime.utcnow().isoformat()))
    con.commit()
    return summary


# ── Agent ─────────────────────────────────────────────────────────────

def chat(con: sqlite3.Connection, user_input: str) -> str:
    memories = recall(con, user_input)
    memory_block = ""
    if memories:
        memory_block = "\n\nRelevant past context:\n" + "\n".join(
            f"[{m['ts'][:10]}] {m['role']}: {m['content']}" for m in memories
        )

    resp = ai.chat.completions.create(
        model="MiniMax-M3",
        messages=[
            {"role": "system", "content":
                "You are a helpful assistant with persistent memory. "
                "Use the past context provided to give informed, consistent answers."
                + memory_block},
            {"role": "user", "content": user_input},
        ],
    )
    return resp.choices[0].message.content


def main():
    con = init_db()
    print("Memory agent ready. Commands: 'digest' for today's summary, 'quit' to exit.\n")

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user:
            continue
        if user.lower() == "quit":
            break
        if user.lower() == "digest":
            print(f"\nToday's digest:\n{get_or_create_digest(con, date.today().isoformat())}\n")
            continue

        store(con, "user", user)
        reply = chat(con, user)
        store(con, "assistant", reply)
        print(f"\nAgent: {reply}\n")


if __name__ == "__main__":
    main()

"""
Multi-agent inbox/outbox pattern — builder + reviewer via file bus.
Run: pip install -r requirements.txt && python run.py "build a hello world FastAPI endpoint"
"""
import os, json, uuid, asyncio
from pathlib import Path
from datetime import datetime
from openai import AsyncOpenAI

MINIMAX_KEY = os.environ["MINIMAX_API_KEY"]
BASE_URL    = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")
BUS         = Path("bus")
(BUS / "inbox/builder").mkdir(parents=True, exist_ok=True)
(BUS / "inbox/reviewer").mkdir(parents=True, exist_ok=True)
(BUS / "outbox").mkdir(parents=True, exist_ok=True)

ai = AsyncOpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)


def _write(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def _read(path: Path) -> dict:
    return json.loads(path.read_text())


async def builder(packet_path: Path) -> Path:
    packet = _read(packet_path)
    print(f"[builder] working on: {packet['task']}")

    resp = await ai.chat.completions.create(
        model="MiniMax-M3",
        messages=[
            {"role": "system", "content": (
                "You are a senior Python engineer. Implement the task. "
                "Return ONLY a JSON object with keys: 'code' (the implementation), "
                "'tests' (pytest tests), 'notes' (brief explanation)."
            )},
            {"role": "user", "content": f"Task: {packet['task']}"},
        ],
        response_format={"type": "json_object"},
    )

    result = json.loads(resp.choices[0].message.content)
    out_path = BUS / f"inbox/reviewer/{packet['id']}.json"
    _write(out_path, json.dumps({**packet, "builder_result": result, "status": "pending_review"}, indent=2))
    packet_path.unlink()
    print(f"[builder] done, sent to reviewer")
    return out_path


async def reviewer(packet_path: Path) -> Path:
    packet = _read(packet_path)
    result = packet["builder_result"]
    print(f"[reviewer] reviewing: {packet['task']}")

    resp = await ai.chat.completions.create(
        model="MiniMax-M3",
        messages=[
            {"role": "system", "content": (
                "You are a staff engineer doing code review. "
                "Review the implementation and tests. "
                "Return JSON with: 'verdict' (passed|needs_revision), "
                "'score' (1-10), 'feedback' (specific actionable feedback)."
            )},
            {"role": "user", "content": (
                f"Task: {packet['task']}\n\n"
                f"Code:\n{result.get('code', '')}\n\n"
                f"Tests:\n{result.get('tests', '')}"
            )},
        ],
        response_format={"type": "json_object"},
    )

    review = json.loads(resp.choices[0].message.content)
    out_path = BUS / f"outbox/{packet['id']}.json"
    _write(out_path, json.dumps({**packet, "review": review,
           "status": review.get("verdict", "needs_revision")}, indent=2))
    packet_path.unlink()
    print(f"[reviewer] verdict: {review.get('verdict')} (score {review.get('score')})")
    return out_path

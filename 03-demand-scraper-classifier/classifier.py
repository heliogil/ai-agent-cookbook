"""
MiniMax M3 signal classifier — scores signals 1-10 against a service portfolio.
"""
import os, json, asyncio
from openai import AsyncOpenAI
from scraper import Signal

MINIMAX_KEY = os.environ["MINIMAX_API_KEY"]
BASE_URL    = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")

client = AsyncOpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)

PORTFOLIO = [
    "AI agent development (Discord bots, automation pipelines)",
    "Web scraping and data collection systems",
    "FastAPI backend services",
    "Multi-agent orchestration",
    "Python automation",
]

SYSTEM = """You are a demand signal classifier. Given a job post or opportunity,
score it 1-10 on three dimensions and return JSON only.

Scoring:
- relevance: how well it matches the portfolio services (1=no match, 10=perfect match)
- budget_signal: evidence of budget (1=no mention, 10=explicit budget stated)
- urgency: how urgently they need help (1=exploring, 10=hire this week)

Return only valid JSON: {"relevance": N, "budget_signal": N, "urgency": N, "summary": "one sentence"}
"""


async def classify(signal: Signal) -> dict:
    portfolio_str = "\n".join(f"- {s}" for s in PORTFOLIO)
    user = f"""Portfolio:\n{portfolio_str}\n\nSignal from {signal.source}:
Title: {signal.title}
Body: {signal.body[:600]}
"""
    try:
        response = await client.chat.completions.create(
            model="MiniMax-M3",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user",   "content": user},
            ],
            response_format={"type": "json_object"},
        )
        scores = json.loads(response.choices[0].message.content)
        scores["score"] = round(
            scores.get("relevance", 0) * 0.5 +
            scores.get("budget_signal", 0) * 0.3 +
            scores.get("urgency", 0) * 0.2,
            1,
        )
        return {**scores, "signal": signal.__dict__}
    except Exception as e:
        return {"score": 0, "error": str(e), "signal": signal.__dict__}


async def classify_all(signals: list[Signal], concurrency: int = 5) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)

    async def bounded(s):
        async with sem:
            return await classify(s)

    results = await asyncio.gather(*[bounded(s) for s in signals])
    return sorted(results, key=lambda x: x.get("score", 0), reverse=True)

"""
Entry point — collect signals, classify, print top results.
"""
import asyncio, json
from scraper import collect_all
from classifier import classify_all

NOTIFY_THRESHOLD = 6.0


async def main():
    print("Collecting signals...")
    signals = await collect_all()
    print(f"Collected {len(signals)} signals. Classifying...")

    results = await classify_all(signals)

    print(f"\n{'='*60}")
    print(f"TOP SIGNALS (score >= {NOTIFY_THRESHOLD})")
    print(f"{'='*60}")

    hot = [r for r in results if r.get("score", 0) >= NOTIFY_THRESHOLD]
    if not hot:
        print("No signals above threshold today.")
    for r in hot:
        s = r["signal"]
        print(f"\n[{r.get('score', 0):.1f}] {s['title']}")
        print(f"  Source   : {s['source']}")
        print(f"  Summary  : {r.get('summary', '')}")
        print(f"  Relevance: {r.get('relevance', 0)} | Budget: {r.get('budget_signal', 0)} | Urgency: {r.get('urgency', 0)}")
        print(f"  URL      : {s['url']}")

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to results.json")


asyncio.run(main())

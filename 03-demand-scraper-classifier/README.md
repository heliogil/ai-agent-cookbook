# 03 — Demand Scraper + Classifier

Scrapes 3 sources (Hacker News jobs, RemoteOK, Product Hunt) and scores each signal against your service portfolio using MiniMax M3.

## What it does

- Collects demand signals from HN "Who is Hiring?", RemoteOK, and Product Hunt
- Classifies each against your portfolio: relevance, budget signal, urgency
- Outputs top signals above a configurable threshold

## Setup

```bash
pip install -r requirements.txt

export MINIMAX_API_KEY=your_key
python main.py
```

## Output example

```
[8.2] Senior Python Engineer @ Acme Corp
  Source   : remoteok
  Summary  : Fast-growing AI startup needs automation pipeline expertise
  Relevance: 9 | Budget: 7 | Urgency: 8
  URL      : https://remoteok.com/...
```

## Customise your portfolio

Edit `PORTFOLIO` in `classifier.py`:

```python
PORTFOLIO = [
    "AI agent development (Discord bots, automation pipelines)",
    "Web scraping and data collection systems",
    # add your services here
]
```

## Add more sources

Implement an async generator following the pattern in `scraper.py`:

```python
async def scrape_mysite(client: httpx.AsyncClient) -> AsyncIterator[Signal]:
    r = await client.get("https://mysite.com/jobs.json")
    for job in r.json():
        yield Signal(source="mysite", title=job["title"], body=job["desc"], url=job["url"])
```

Then add it to the `scrapers` list in `collect_all()`.

## Run on a schedule

```bash
# cron: run every 6 hours
0 */6 * * * cd /path/to/03-demand-scraper-classifier && python main.py >> demand.log 2>&1
```

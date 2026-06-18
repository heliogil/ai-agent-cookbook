"""
Multi-source demand scraper — httpx + BeautifulSoup, rate-limited.
"""
import asyncio, httpx
from dataclasses import dataclass
from typing import AsyncIterator
from bs4 import BeautifulSoup


@dataclass
class Signal:
    source: str
    title: str
    body: str
    url: str


HEADERS = {"User-Agent": "DemandScanner/1.0 (research bot; +https://github.com/heliogil)"}


async def scrape_hn_jobs(client: httpx.AsyncClient) -> AsyncIterator[Signal]:
    """Hacker News 'Who is Hiring?' — current month thread."""
    r = await client.get("https://hacker-news.firebaseio.com/v0/user/whoishiring.json")
    uid = r.json()
    user = await client.get(f"https://hacker-news.firebaseio.com/v0/user/{uid}.json")
    submitted = user.json().get("submitted", [])[:1]  # latest thread only

    for thread_id in submitted:
        thread = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{thread_id}.json")
        kids   = thread.json().get("kids", [])[:50]   # first 50 comments

        tasks = [client.get(f"https://hacker-news.firebaseio.com/v0/item/{k}.json") for k in kids]
        results = await asyncio.gather(*tasks)
        for res in results:
            item = res.json()
            if item and item.get("text"):
                soup = BeautifulSoup(item["text"], "html.parser")
                yield Signal(
                    source="hackernews",
                    title="HN: Who is Hiring?",
                    body=soup.get_text()[:800],
                    url=f"https://news.ycombinator.com/item?id={item['id']}",
                )


async def scrape_remoteok(client: httpx.AsyncClient) -> AsyncIterator[Signal]:
    """RemoteOK job board."""
    r = await client.get("https://remoteok.com/api", headers=HEADERS)
    jobs = r.json()
    for job in jobs[1:21]:  # skip first (legal notice), take 20
        if not isinstance(job, dict):
            continue
        yield Signal(
            source="remoteok",
            title=f"{job.get('position', '')} @ {job.get('company', '')}",
            body=BeautifulSoup(job.get("description", ""), "html.parser").get_text()[:800],
            url=job.get("url", ""),
        )


async def scrape_producthunt(client: httpx.AsyncClient) -> AsyncIterator[Signal]:
    """Product Hunt daily top launches (RSS)."""
    r = await client.get("https://www.producthunt.com/feed", headers=HEADERS)
    soup = BeautifulSoup(r.text, "xml")
    for item in soup.find_all("item")[:10]:
        yield Signal(
            source="producthunt",
            title=item.find("title").text if item.find("title") else "",
            body=item.find("description").text[:800] if item.find("description") else "",
            url=item.find("link").text if item.find("link") else "",
        )


async def collect_all() -> list[Signal]:
    signals: list[Signal] = []
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        scrapers = [scrape_hn_jobs, scrape_remoteok, scrape_producthunt]
        for scraper in scrapers:
            try:
                async for signal in scraper(client):
                    signals.append(signal)
                await asyncio.sleep(1)  # polite delay between sources
            except Exception as e:
                print(f"[{scraper.__name__}] error: {e}")
    return signals

"""
Layer 1 -- Ingestion.
Pulls the free public RSS feeds plus a Google-News-RSS workaround for the
four paywalled sources, dedups by URL, and writes data/candidates.json.

No API key needed for this step -- everything here is a public RSS feed.
"""
import json
import time
import urllib.parse
from pathlib import Path

import feedparser
import requests
import yaml
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
OUT = ROOT / "data" / "candidates.json"

MAX_AGE_HOURS = CONFIG["scoring"]["max_age_hours"]
NOW = time.time()


def _age_ok(published_struct):
    if not published_struct:
        return True  # keep items with no parseable date rather than drop them
    try:
        ts = time.mktime(published_struct)
        return (NOW - ts) <= MAX_AGE_HOURS * 3600
    except (OverflowError, ValueError):
        return True


def fetch_rss(name, url, tier):
    items = []
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[warn] could not fetch {name}: {e}")
        return items
    for entry in feed.entries:
        if not _age_ok(entry.get("published_parsed")):
            continue
        items.append({
            "source": name,
            "tier": tier,
            "title": entry.get("title", "").strip(),
            "summary": (entry.get("summary", "") or "").strip()[:600],
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
        })
    return items


def fetch_google_news(name, query):
    """Headline + snippet only, via Google News' public RSS search endpoint.
    This reads a public aggregator feed -- it does not scrape the paywalled
    article page itself."""
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    items = []
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[warn] could not fetch Google News for {name}: {e}")
        return items
    for entry in feed.entries[:8]:
        if not _age_ok(entry.get("published_parsed")):
            continue
        items.append({
            "source": name,
            "tier": 1,
            "title": entry.get("title", "").strip(),
            "summary": (entry.get("summary", "") or "").strip()[:600],
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
        })
    return items


def main():
    candidates = []
    for feed in CONFIG["rss_feeds"]:
        candidates.extend(fetch_rss(feed["name"], feed["url"], feed["tier"]))
        time.sleep(0.5)  # be polite

    for topic in CONFIG["google_news_topics"]:
        candidates.extend(fetch_google_news(topic["name"], topic["query"]))
        time.sleep(0.5)

    # Dedup by link, then by near-identical title
    seen_links, seen_titles, deduped = set(), set(), []
    for c in candidates:
        key_title = c["title"].lower()[:80]
        if c["link"] in seen_links or key_title in seen_titles:
            continue
        seen_links.add(c["link"])
        seen_titles.add(key_title)
        deduped.append(c)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(deduped, indent=2))
    print(f"Fetched {len(deduped)} candidate items -> {OUT}")


if __name__ == "__main__":
    main()

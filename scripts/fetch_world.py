"""
Layer 1b -- world-news ingestion for the second video.

Separate from fetch_news.py on purpose: that one feeds the business
briefing and works; this adds global sources without touching it.

Produces data/world_shortlist.json with 10 India + 10 non-India stories,
scored for "does this move markets or reach my life" -- tariffs, war,
rates, AI, layoffs, recession, energy, supply chains.
"""
import json
import re
import time
from pathlib import Path

import feedparser
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
OUT = ROOT / "data" / "world_shortlist.json"

WORLD = CONFIG.get("world", {})
FEEDS = WORLD.get("feeds", [])
PER_REGION = WORLD.get("per_region", 10)
MAX_AGE_HOURS = WORLD.get("max_age_hours", 36)

IMPACT_KEYWORDS = [
    "tariff", "trade war", "sanction", "export ban", "supply chain",
    "inflation", "interest rate", "rate cut", "rate hike", "central bank",
    "fed", "recession", "slowdown", "gdp", "layoff", "job cuts", "hiring",
    "ai", "artificial intelligence", "chip", "semiconductor", "data centre",
    "data center", "oil", "crude", "energy", "gas price", "currency",
    "rupee", "dollar", "war", "conflict", "strike", "election", "brics",
    "imf", "world bank", "stock market", "equities", "bond", "crash",
    "crisis", "default", "merger", "acquisition", "ipo", "regulation",
]


def score(entry_text, published_ts):
    text = entry_text.lower()
    hits = sum(1 for k in IMPACT_KEYWORDS if k in text)
    impact = min(hits / 4.0, 1.0)
    age_h = (time.time() - published_ts) / 3600 if published_ts else 999
    recency = max(0.0, 1.0 - age_h / MAX_AGE_HOURS)
    return round(0.7 * impact + 0.3 * recency, 3)


def clean(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def main():
    buckets = {"india": [], "global": []}

    for feed in FEEDS:
        region = feed.get("region", "global")
        try:
            parsed = feedparser.parse(feed["url"])
        except Exception as e:
            print(f"[warn] {feed['name']} failed: {e}")
            continue
        for e in parsed.entries[:40]:
            ts = None
            if getattr(e, "published_parsed", None):
                ts = time.mktime(e.published_parsed)
            if ts and (time.time() - ts) / 3600 > MAX_AGE_HOURS:
                continue
            title = clean(getattr(e, "title", ""))
            summary = clean(getattr(e, "summary", ""))[:400]
            if not title:
                continue
            buckets[region].append({
                "title": title,
                "link": getattr(e, "link", ""),
                "summary": summary,
                "source": feed["name"],
                "region": region,
                "scores": {"total": score(title + " " + summary, ts)},
            })

    shortlist = []
    for region in ("india", "global"):
        items = sorted(buckets[region], key=lambda x: x["scores"]["total"], reverse=True)
        seen, picked = set(), []
        for it in items:
            key = it["title"].lower()[:60]
            if key in seen:
                continue
            seen.add(key)
            picked.append(it)
            if len(picked) >= PER_REGION:
                break
        shortlist.extend(picked)
        print(f"{region}: {len(picked)} of {len(buckets[region])} candidates")

    OUT.write_text(json.dumps(shortlist, indent=2))
    print(f"Wrote {len(shortlist)} world stories -> {OUT}")


if __name__ == "__main__":
    main()

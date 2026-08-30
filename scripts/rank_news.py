"""
Layer 2 -- Dedup & CXO-relevance ranking.
Pure rule-based scoring (keyword matching + source tier + recency) --
deliberately NOT an LLM call, so this step costs nothing and needs no key.
Mirrors the formula from the blueprint doc:
  score = 0.40*cxo + 0.25*career + 0.20*source_recency + 0.15*category
"""
import json
import time
from pathlib import Path

import yaml
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
IN = ROOT / "data" / "candidates.json"
OUT = ROOT / "data" / "shortlist.json"

W = CONFIG["scoring"]["weights"]
CXO_KW = [k.lower() for k in CONFIG["scoring"]["cxo_keywords"]]
CAREER_KW = [k.lower() for k in CONFIG["scoring"]["career_keywords"]]
SHORTLIST_SIZE = CONFIG["scoring"]["shortlist_size"]


def keyword_score(text, keywords):
    text = text.lower()
    hits = sum(1 for k in keywords if k in text)
    return min(10, hits * 2.5)  # 4+ distinct keyword hits caps the score at 10


def recency_score(published_str):
    if not published_str:
        return 5.0  # neutral if unknown
    try:
        dt = dateparser.parse(published_str)
        age_hours = (time.time() - dt.timestamp()) / 3600
        if age_hours <= 6:
            return 10.0
        if age_hours <= 12:
            return 8.0
        if age_hours <= 24:
            return 6.0
        return 3.0
    except Exception:
        return 5.0


def tier_score(tier):
    return 10.0 if tier == 1 else 7.0


def main():
    candidates = json.loads(IN.read_text())
    scored = []
    for c in candidates:
        text = f"{c['title']} {c['summary']}"
        cxo = keyword_score(text, CXO_KW)
        career = keyword_score(text, CAREER_KW)
        src_rec = 0.5 * tier_score(c["tier"]) + 0.5 * recency_score(c["published"])
        category = 10.0  # every feed here is already a business/finance/startup feed
        total = (W["cxo_relevance"] * cxo + W["career_relevance"] * career
                 + W["source_recency"] * src_rec + W["category_fit"] * category)
        c["scores"] = {"cxo": cxo, "career": career, "source_recency": round(src_rec, 2),
                        "category": category, "total": round(total, 2)}
        scored.append(c)

    scored.sort(key=lambda x: x["scores"]["total"], reverse=True)
    shortlist = scored[:SHORTLIST_SIZE]

    OUT.write_text(json.dumps(shortlist, indent=2))
    print(f"Ranked {len(scored)} items, shortlisted top {len(shortlist)} -> {OUT}")
    for s in shortlist[:5]:
        print(f"  {s['scores']['total']:5.2f}  {s['source']:<20} {s['title'][:70]}")


if __name__ == "__main__":
    main()

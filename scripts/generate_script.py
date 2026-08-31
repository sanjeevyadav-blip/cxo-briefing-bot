"""
Layer 3 -- Script generation.
Uses the Groq API (free tier, open-weight models such as Llama 3.3) --
this is intentionally NOT Anthropic/Claude, per the "no Claude tokens in
the automation" requirement. Needs GROQ_API_KEY as a GitHub secret;
sign-up is free at console.groq.com and does not require a credit card
at the time of writing -- reverify before you rely on it.

Two Groq calls per day: one writes the two-host banter script, a second
writes a plain ~100-word summary per shortlisted article for the website
(separate call so a parsing hiccup in one doesn't break the other).

If you'd rather have zero external API calls at all, see the
"fully local" note at the bottom of this file.
"""
import json
import os
import re
from pathlib import Path

import yaml
from groq import Groq

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
SHORTLIST = json.loads((ROOT / "data" / "shortlist.json").read_text())
OUT_SCRIPT = ROOT / "data" / "script.json"
OUT_NOTES = ROOT / "data" / "show_notes.md"

TARGET_WORDS = CONFIG["episode"]["target_word_count"]
MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b-versatile was deprecated by Groq
# on 17 Jun 2026; this is Groq's recommended replacement. Swap freely for
# any other Groq-hosted model -- check console.groq.com/docs/models for
# the current list if this one ever gets retired too.

SYSTEM_PROMPT = f"""You write a daily two-host business news podcast script for an Indian
analytics manager moving toward a Data Science / Head-of-Business career track.

Hosts:
- [A]: skeptical, numbers-first, asks the "wait, really?" questions
- [B]: explains consequences and connects stories together

Rules:
- Target length: about {TARGET_WORDS} words total.
- Cover ALL the stories given below, not just a few -- keep the cold open
  and sign-off brief so most of the runtime goes to actual news, with
  concrete numbers, names, and context per story rather than a passing
  mention.
- Every number, name, and claim must come from the supplied items --
  never invent a figure.
- Segments, in order: cold open (very short, under 30 seconds), Markets &
  Macro, one Big Story deep-dive, Startup & Funding pulse,
  Corporate/Regulatory bites, a 90-second "career nugget" tying today's
  news to data-science/analytics-leadership career relevance, then a
  brief sign-off.
- Tone: witty, fast-paced banter -- like two sharp friends, not a news anchor.
- Language level: plain, everyday English. Short sentences. Avoid idioms,
  Western pop-culture references, and jargon that isn't explained in the
  same breath -- the audience includes people who know English well but
  aren't native or professional-level speakers.
- Output STRICTLY as alternating lines, each starting with "[A]" or "[B]",
  nothing else -- no headers, no stage directions, no markdown."""

SUMMARY_SYSTEM_PROMPT = """Write a plain-English summary of about 100 words for each numbered
news item below. Stick strictly to facts given in that item -- never
invent a number, name, or detail. Keep it factual and readable, not
banter. Output STRICTLY as a numbered list matching the input numbers,
one paragraph per item, nothing else -- no headers, no extra commentary,
no markdown formatting."""


def build_user_prompt():
    lines = []
    for i, item in enumerate(SHORTLIST, 1):
        lines.append(
            f"{i}. ({item['source']}, score {item['scores']['total']}) "
            f"{item['title']} -- {item['summary']}"
        )
    return "Today's shortlisted stories:\n" + "\n".join(lines)


def parse_script(raw_text):
    turns = []
    for line in raw_text.splitlines():
        line = line.strip()
        m = re.match(r"^\[(A|B)\]\s*(.+)$", line)
        if m:
            turns.append({"speaker": m.group(1), "text": m.group(2).strip()})
    return turns


def parse_summaries(raw_text):
    """Parses a numbered list into {index: summary_text}, tolerating
    summaries that wrap across multiple lines before the next number."""
    summaries = {}
    current_num = None
    current_lines = []
    for line in raw_text.splitlines():
        m = re.match(r"^(\d+)[.)]\s*(.*)$", line.strip())
        if m:
            if current_num is not None:
                summaries[current_num] = " ".join(current_lines).strip()
            current_num = int(m.group(1))
            current_lines = [m.group(2)] if m.group(2) else []
        elif line.strip() and current_num is not None:
            current_lines.append(line.strip())
    if current_num is not None:
        summaries[current_num] = " ".join(current_lines).strip()
    return summaries


def generate_summaries(client):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt()},
        ],
        temperature=0.4,
        max_tokens=4000,
    )
    raw = resp.choices[0].message.content
    (ROOT / "data" / "summaries_raw.txt").write_text(raw)
    return parse_summaries(raw)


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY is not set -- add it as a GitHub Actions secret.")

    client = Groq(api_key=api_key)
    resp = client.chat.

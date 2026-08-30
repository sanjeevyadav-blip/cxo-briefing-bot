"""
Layer 3 -- Script generation.
Uses the Groq API (free tier, open-weight models such as Llama 3.3) --
this is intentionally NOT Anthropic/Claude, per the "no Claude tokens in
the automation" requirement. Needs GROQ_API_KEY as a GitHub secret;
sign-up is free at console.groq.com and does not require a credit card
at the time of writing -- reverify before you rely on it.

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
- Cover ONLY the stories given below. Every number, name, and claim must come
  from the supplied items -- never invent a figure.
- Segments, in order: cold open (short), Markets & Macro, one Big Story
  deep-dive, Startup & Funding pulse, Corporate/Regulatory bites, a 2-minute
  "career nugget" tying today's news to data-science/analytics-leadership
  career relevance, then a sign-off.
- Tone: witty, fast-paced banter -- like two sharp friends, not a news anchor.
- Language level: plain, everyday English. Short sentences. Avoid idioms,
  Western pop-culture references, and jargon that isn't explained in the
  same breath -- the audience includes people who know English well but
  aren't native or professional-level speakers.
- Output STRICTLY as alternating lines, each starting with "[A]" or "[B]",
  nothing else -- no headers, no stage directions, no markdown."""


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


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY is not set -- add it as a GitHub Actions secret.")

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt()},
        ],
        temperature=0.8,
        max_tokens=6000,
    )
    raw = resp.choices[0].message.content
    turns = parse_script(raw)
    if not turns:
        raise SystemExit("Model output didn't parse into [A]/[B] turns -- check data/script_raw.txt")

    (ROOT / "data" / "script_raw.txt").write_text(raw)
    OUT_SCRIPT.write_text(json.dumps(turns, indent=2))

    notes = ["# Show notes -- source articles\n"]
    for item in SHORTLIST:
        notes.append(f"- [{item['title']}]({item['link']}) -- {item['source']}")
    OUT_NOTES.write_text("\n".join(notes))

    word_count = sum(len(t["text"].split()) for t in turns)
    print(f"Generated {len(turns)} turns, ~{word_count} words -> {OUT_SCRIPT}")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# Fully-local alternative (zero external API calls of any kind):
# Replace the Groq call above with llama-cpp-python running a small quantized
# open model (e.g. Llama-3.2-3B-Instruct-Q4_K_M.gguf) downloaded once and
# cached via actions/cache in the workflow. It's slower (several minutes on
# a GitHub-hosted CPU runner) and the writing quality is noticeably below a
# 70B-class hosted model, but it has no external dependency whatsoever.
# Ask if you want this variant fully written out.
# ---------------------------------------------------------------------------

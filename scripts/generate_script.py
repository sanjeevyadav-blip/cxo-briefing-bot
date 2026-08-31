"""
Layer 3 -- Script generation, via the Groq API (free tier, open-weight
models). Intentionally NOT Anthropic/Claude, per the "no Claude tokens in
the automation" requirement. Needs GROQ_API_KEY as a GitHub secret.

Two Groq calls per day: one writes the two-host banter script, a second
writes a plain ~100-word summary per shortlisted article for the website
(separate call so a parsing hiccup in one doesn't break the other).

Prompt text lives in scripts/prompts.py.
"""
import json
import os
import re
from pathlib import Path

import yaml
from groq import Groq

from prompts import SUMMARY_SYSTEM_PROMPT, SYSTEM_PROMPT_TEMPLATE

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
SHORTLIST = json.loads((ROOT / "data" / "shortlist.json").read_text())
OUT_SCRIPT = ROOT / "data" / "script.json"
OUT_NOTES = ROOT / "data" / "show_notes.md"

TARGET_WORDS = CONFIG["episode"]["target_word_count"]
# llama-3.3-70b-versatile was deprecated by Groq on 17 Jun 2026; this is
# their recommended replacement. See console.groq.com/docs/models.
MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE.format(target_words=TARGET_WORDS)


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
        m = re.match(r"^\[(A|B)\]\s*(.+)$", line.strip())
        if m:
            turns.append({"speaker": m.group(1), "text": m.group(2).strip()})
    return turns


def parse_summaries(raw_text):
    """Numbered list -> {index: summary}, tolerating wrapped lines."""
    summaries = {}
    num = None
    buf = []
    for line in raw_text.splitlines():
        m = re.match(r"^(\d+)[.)]\s*(.*)$", line.strip())
        if m:
            if num is not None:
                summaries[num] = " ".join(buf).strip()
            num = int(m.group(1))
            buf = [m.group(2)] if m.group(2) else []
        elif line.strip() and num is not None:
            buf.append(line.strip())
    if num is not None:
        summaries[num] = " ".join(buf).strip()
    return summaries


def ask(client, system_prompt, temperature, max_tokens):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": build_user_prompt()},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY is not set -- add it as an Actions secret.")

    client = Groq(api_key=api_key)

    raw = ask(client, SYSTEM_PROMPT, 0.8, 7000)
    turns = parse_script(raw)
    if not turns:
        raise SystemExit("Output didn't parse into [A]/[B] turns -- see script_raw.txt")
    (ROOT / "data" / "script_raw.txt").write_text(raw)
    OUT_SCRIPT.write_text(json.dumps(turns, indent=2))

    # Summaries are best-effort: a failure here still leaves a usable
    # episode, the site just shows links without summaries that day.
    try:
        raw_sum = ask(client, SUMMARY_SYSTEM_PROMPT, 0.4, 4000)
        (ROOT / "data" / "summaries_raw.txt").write_text(raw_sum)
        summaries = parse_summaries(raw_sum)
    except Exception as e:
        print(f"[warn] summary generation failed, continuing: {e}")
        summaries = {}

    notes = ["# Show notes -- source articles\n"]
    for i, item in enumerate(SHORTLIST, 1):
        notes.append(f"## [{item['title']}]({item['link']}) -- {item['source']}")
        summary = summaries.get(i, "").strip()
        if summary:
            notes.append(summary)
        notes.append("")
    OUT_NOTES.write_text("\n".join(notes))

    words = sum(len(t["text"].split()) for t in turns)
    print(f"Generated {len(turns)} turns, ~{words} words, "
          f"{len(summaries)}/{len(SHORTLIST)} summaries -> {OUT_SCRIPT}")


if __name__ == "__main__":
    main()

"""
Layer 3b -- scripts for the two extra videos.

  python gen_extra.py world       -> script_world.json + world_summaries.json
  python gen_extra.py explainer   -> script_explainer.json

Kept separate from generate_script.py so the working business briefing is
never at risk from changes here. Reuses the same [A]/[B] two-host format,
so tts_render.py renders these with no changes.

Groq's free tier caps 8000 tokens/minute, so every call waits out the
window first -- the run is slower but never hits a 413.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import yaml
from groq import Groq

from prompts import EXPLAINER_PROMPT, SUMMARY_SYSTEM_PROMPT, WORLD_PROMPT

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
DATA = ROOT / "data"
MODEL = "openai/gpt-oss-120b"


def parse_turns(raw):
    turns = []
    for line in raw.splitlines():
        m = re.match(r"^\[(A|B)\]\s*(.+)$", line.strip())
        if m:
            turns.append({"speaker": m.group(1), "text": m.group(2).strip()})
    return turns


def parse_summaries(raw):
    """Numbered list -> {index: summary}, tolerating wrapped lines."""
    out, num, buf = {}, None, []
    for line in raw.splitlines():
        m = re.match(r"^(\d+)[.)]\s*(.*)$", line.strip())
        if m:
            if num is not None:
                out[num] = " ".join(buf).strip()
            num = int(m.group(1))
            buf = [m.group(2)] if m.group(2) else []
        elif line.strip() and num is not None:
            buf.append(line.strip())
    if num is not None:
        out[num] = " ".join(buf).strip()
    return out


def stories_block(items):
    lines = []
    for i, it in enumerate(items, 1):
        region = f", {it['region']}" if it.get("region") else ""
        lines.append(f"{i}. ({it['source']}{region}) {it['title']} -- {it['summary']}")
    return "\n".join(lines)


def ask(client, system_prompt, user_prompt, max_tokens):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=max_tokens,
        reasoning_effort="low",
    )
    return resp.choices[0].message.content or ""


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "world"
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY is not set.")
    client = Groq(api_key=api_key)

    words = CONFIG["episode"].get("extra_word_count", 1800)

    if kind == "world":
        items = json.loads((DATA / "world_shortlist.json").read_text())
        system = WORLD_PROMPT.format(target_words=words)
        user = "Today's world stories:\n" + stories_block(items)
        out = DATA / "script_world.json"
        raw_out = DATA / "script_world_raw.txt"
    else:
        items = json.loads((DATA / "shortlist.json").read_text())[:2]
        system = EXPLAINER_PROMPT
        user = "Explain these two stories:\n" + stories_block(items)
        out = DATA / "script_explainer.json"
        raw_out = DATA / "script_explainer_raw.txt"

    time.sleep(65)   # wait out the tokens-per-minute window
    raw = ask(client, system, user, 5000)
    raw_out.write_text(raw)

    turns = parse_turns(raw)
    if not turns:
        raise SystemExit(
            f"{kind}: no [A]/[B] turns. Got {len(raw)} chars. "
            f"First 400:\n{raw[:400]}"
        )
    out.write_text(json.dumps(turns, indent=2))

    wc = sum(len(t["text"].split()) for t in turns)
    print(f"{kind}: {len(turns)} turns, ~{wc} words -> {out}")

    # World news also gets a ~100-word summary per story for the website.
    # Best-effort: a failure here still leaves a usable video.
    if kind == "world":
        try:
            time.sleep(65)
            raw_sum = ask(client, SUMMARY_SYSTEM_PROMPT, user, 3500)
            (DATA / "world_summaries_raw.txt").write_text(raw_sum)
            sums = parse_summaries(raw_sum)
            merged = {str(i): sums.get(i, "") for i in range(1, len(items) + 1)}
            (DATA / "world_summaries.json").write_text(json.dumps(merged, indent=2))
            print(f"world summaries: {sum(1 for v in merged.values() if v)}"
                  f"/{len(items)}")
        except Exception as e:
            print(f"[warn] world summaries failed, continuing: {e}")


if __name__ == "__main__":
    main()

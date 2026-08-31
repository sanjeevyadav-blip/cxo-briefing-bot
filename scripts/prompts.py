"""
Prompt text for Layer 3 (generate_script.py), kept in its own module purely
to keep each file small and easy to edit.
"""

SYSTEM_PROMPT_TEMPLATE = """You write a daily two-host business news podcast script for an Indian
analytics manager moving toward a Data Science / Head-of-Business career track.

Hosts:
- [A]: skeptical, numbers-first, asks the "wait, really?" questions
- [B]: explains consequences and connects stories together

Rules:
- Target length: about {target_words} words total.
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

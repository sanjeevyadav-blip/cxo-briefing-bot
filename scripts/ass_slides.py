"""
Building blocks for the explainer slides (see explainer_slides.py).

Per story: a label ("STORY 3 OF 20"), the headline, up to three bullet
points that appear one at a time while the story is discussed, and the
key number in a highlight panel. An intro slide covers the opening before
the first story. The spoken line runs as a caption at the bottom.
"""
import slide_style as st

WORDS_PER_CAP = 14
PANEL = "&H2A221C&"

_FMT = ",".join([
    "Name", "Fontname", "Fontsize", "PrimaryColour", "OutlineColour",
    "BackColour", "Bold", "BorderStyle", "Outline", "Shadow",
    "Alignment", "MarginL", "MarginR", "MarginV", "Encoding",
])
_EVT = ",".join([
    "Layer", "Start", "End", "Style", "Name",
    "MarginL", "MarginR", "MarginV", "Effect", "Text",
])
HEADER = "\n".join([
    "[Script Info]", "ScriptType: v4.00+",
    "PlayResX: 1280", "PlayResY: 720", "WrapStyle: 2", "",
    "[V4+ Styles]", "Format: " + _FMT,
    "Style: Base,DejaVu Sans,30,&H00F3EDE6,&H0,&H0,1,1,0,0,7,0,0,0,1",
    "Style: Cap,DejaVu Sans,26,&H00B8B8B8,&H0,&H0,0,1,2,0,2,120,120,62,1",
    "", "[Events]", "Format: " + _EVT, "",
])


def ass_time(s):
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def clean(t):
    return (t or "").replace("{", "(").replace("}", ")").replace("\n", " ")


def wrap(text, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\\N".join(lines[:max_lines])


def stat_size(text):
    """Shrink long figures so they stay inside the 304px panel."""
    n = len(text)
    return 46 if n <= 9 else 38 if n <= 12 else 30 if n <= 16 else 24


def ev(layer, a, b, body, style="Base"):
    return f"Dialogue: {layer},{a},{b},{style},,0,0,0,,{body}"


def captions(timeline):
    caps = []
    for item in timeline:
        words = item["text"].split()
        groups = [words[i:i + WORDS_PER_CAP]
                  for i in range(0, len(words), WORDS_PER_CAP)] or [[""]]
        total = sum(len(" ".join(g)) for g in groups) or 1
        span = max(item["end"] - item["start"], 0.1)
        t = item["start"]
        for g in groups:
            text = " ".join(g)
            share = span * len(text) / total
            caps.append((t, t + share, text, item["speaker"]))
            t += share
    return caps

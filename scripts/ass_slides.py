"""
Slide generation for make_video.py.

Each story gets a designed card: accent bar, big story number and count,
the headline left-aligned, a source chip, and a divider above the spoken
caption. The accent colour changes per story, and the card changes when
the conversation moves on. Visual constants live in slide_style.py.
"""
import slide_style as st

WORDS_PER_CARD = 14
HEADLINE_CHARS = 38

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
    "[Script Info]",
    "ScriptType: v4.00+",
    "PlayResX: 1280",
    "PlayResY: 720",
    "WrapStyle: 2",
    "",
    "[V4+ Styles]",
    "Format: " + _FMT,
    "Style: Base,DejaVu Sans,30,&H00F3EDE6,&H0,&H0,1,1,0,0,7,0,0,0,1",
    "Style: Cap,DejaVu Sans,30,&H00D0D0D0,&H0,&H0,0,1,2,0,2,120,120,72,1",
    "",
    "[Events]",
    "Format: " + _EVT,
    "",
])


def ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def clean(text):
    return (text or "").replace("{", "(").replace("}", ")").replace("\n", " ")


def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\\N".join(lines[:3])


def caption_cards(timeline):
    cards = []
    for item in timeline:
        words = item["text"].split()
        step = WORDS_PER_CARD
        groups = [words[i:i + step] for i in range(0, len(words), step)]
        groups = groups or [[""]]
        total = sum(len(" ".join(g)) for g in groups) or 1
        span = max(item["end"] - item["start"], 0.1)
        t = item["start"]
        for g in groups:
            text = " ".join(g)
            share = span * (len(text) / total)
            cards.append((t, t + share, text, item["speaker"]))
            t += share
    return cards


def ev(layer, a, b, body, style="Base"):
    return f"Dialogue: {layer},{a},{b},{style},,0,0,0,,{body}"


def card_events(a, b, story, idx, total):
    col = st.accent(idx)
    head = wrap(clean(story.get("title", "")), HEADLINE_CHARS)
    src = clean(story.get("source", ""))
    return [
        ev(0, a, b, st.rect(96, 150, 10, 300, col)),
        ev(0, a, b, st.text_at(130, 138, f"{idx + 1:02d}", col, 72)),
        ev(0, a, b, st.text_at(250, 170, f"of {total}", st.DIM, 26, 0)),
        ev(0, a, b, st.text_at(130, 240, head, st.PAPER, 46)),
        ev(0, a, b, st.rect(130, 470, 14, 14, col)),
        ev(0, a, b, st.text_at(156, 461, src, st.DIM, 26)),
    ]


def write_ass(timeline, story_spans, stories, title, subtitle, path):
    caps = caption_cards(timeline)
    end_all = max((c[1] for c in caps), default=1.0) + 2
    z, e = ass_time(0), ass_time(end_all)
    out = [
        ev(0, z, e, st.text_at(96, 40, clean(title), st.PAPER, 28)),
        ev(0, z, e, st.text_at(1184, 40, subtitle, st.DIM, 26, 0, 9)),
        ev(0, z, e, st.rect(96, 88, 1088, 2, st.RULE)),
        ev(0, z, e, st.rect(96, 560, 1088, 2, st.RULE)),
    ]
    for start, end, idx in story_spans:
        out += card_events(ass_time(start), ass_time(end),
                           stories[idx], idx, len(stories))
    for start, end, text, speaker in caps:
        a, b = ass_time(start), ass_time(end)
        out.append(ev(1, a, b, clean(text), "Cap"))
        out.append(ev(1, a, b, st.text_at(1184, 680, f"Host {speaker}",
                                          st.DIM, 22, 1, 3)))
    path.write_text(HEADER + "\n".join(out) + "\n")

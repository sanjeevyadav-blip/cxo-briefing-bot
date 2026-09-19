"""
Slide/subtitle generation for make_video.py -- kept in its own module so
each file stays small.

Turns a timeline of spoken lines into short on-screen cards and writes an
ASS subtitle file. Each card's duration is shared out by character count,
so text tracks speech closely without real word-level alignment.
"""

WORDS_PER_CARD = 14

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
    "WrapStyle: 0",
    "",
    "[V4+ Styles]",
    "Format: " + _FMT,
    "Style: Head,DejaVu Sans,34,&H00A6A6A6,&H0,&H0,1,1,0,0,8,60,60,40,1",
    "Style: Body,DejaVu Sans,46,&H00F3EDE6,&H0,&H0,1,1,3,0,5,90,90,90,1",
    "Style: Tag,DejaVu Sans,28,&H0088B0FF,&H0,&H0,1,1,0,0,2,60,60,50,1",
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


def cards_from_timeline(timeline):
    """Split each line into short cards, sharing its duration by length."""
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


def write_ass(cards, title, subtitle, path):
    end_all = max((c[1] for c in cards), default=1.0) + 2
    lines = []
    lines.append(
        f"Dialogue: 0,{ass_time(0)},{ass_time(end_all)},Head,,0,0,0,,"
        f"{title}  |  {subtitle}"
    )
    for start, end, text, speaker in cards:
        safe = text.replace("{", "(").replace("}", ")")
        a, b = ass_time(start), ass_time(end)
        lines.append(f"Dialogue: 0,{a},{b},Body,,0,0,0,,{safe}")
        lines.append(f"Dialogue: 0,{a},{b},Tag,,0,0,0,,Host {speaker}")
    path.write_text(HEADER + "\n".join(lines) + "\n")

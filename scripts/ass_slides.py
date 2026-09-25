"""
Slide generation for make_video.py.

Each story gets a card: the headline large in the upper half, the source
under it, and the spoken line as a caption at the bottom. The card changes
when the conversation moves to the next story, so the video reads like a
deck rather than a wall of subtitles.
"""
WORDS_PER_CARD = 14
HEADLINE_CHARS = 42

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
    "Style: Head,DejaVu Sans,30,&H00909090,&H0,&H0,1,1,0,0,8,60,60,34,1",
    "Style: Card,DejaVu Sans,50,&H00F3EDE6,&H0,&H0,1,1,0,0,8,90,90,150,1",
    "Style: Src,DejaVu Sans,28,&H0088B0FF,&H0,&H0,1,1,0,0,8,90,90,400,1",
    "Style: Cap,DejaVu Sans,32,&H00C8C8C8,&H0,&H0,0,1,2,0,2,110,110,70,1",
    "Style: Tag,DejaVu Sans,24,&H00707070,&H0,&H0,1,1,0,0,2,60,60,28,1",
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
    """Hard-wrap a headline into ASS line breaks so it never overflows."""
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
    """Split each spoken line into short caption cards, sharing that
    line's duration between them by character count."""
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


def write_ass(timeline, story_spans, stories, title, subtitle, path):
    caps = caption_cards(timeline)
    end_all = max((c[1] for c in caps), default=1.0) + 2
    out = [
        f"Dialogue: 0,{ass_time(0)},{ass_time(end_all)},Head,,0,0,0,,"
        f"{clean(title)}  |  {subtitle}"
    ]
    for start, end, idx in story_spans:
        story = stories[idx]
        a, b = ass_time(start), ass_time(end)
        out.append(f"Dialogue: 0,{a},{b},Card,,0,0,0,,"
                   f"{wrap(clean(story.get('title', '')), HEADLINE_CHARS)}")
        out.append(f"Dialogue: 0,{a},{b},Src,,0,0,0,,"
                   f"{clean(story.get('source', ''))}")
    for start, end, text, speaker in caps:
        a, b = ass_time(start), ass_time(end)
        out.append(f"Dialogue: 1,{a},{b},Cap,,0,0,0,,{clean(text)}")
        out.append(f"Dialogue: 1,{a},{b},Tag,,0,0,0,,Host {speaker}")
    path.write_text(HEADER + "\n".join(out) + "\n")

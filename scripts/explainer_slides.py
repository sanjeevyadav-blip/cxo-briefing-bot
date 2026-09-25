"""
Explainer-style slide layout, like a YouTube news explainer.

Per story: a label ("STORY 3 OF 20"), the headline, up to three bullet
points that appear one at a time while the story is discussed, and the
key number in a highlight panel. An intro slide covers the opening. The
building blocks (timing, wrapping, captions) live in ass_slides.py.
"""
import slide_style as st
from ass_slides import (HEADER, PANEL, ass_time, captions, clean, ev,
                        stat_size, wrap)


def intro_events(a, b, title, n):
    return [
        ev(0, a, b, st.text_at(96, 200, "TODAY'S BRIEFING", st.DIM, 26)),
        ev(0, a, b, st.text_at(96, 250, clean(title), st.PAPER, 64)),
        ev(0, a, b, st.rect(96, 350, 120, 6, st.accent(0))),
        ev(0, a, b, st.text_at(96, 380, f"{n} stories", st.DIM, 32, 0)),
    ]


def story_events(start, end, slide, idx, total):
    col = st.accent(idx)
    a, b = ass_time(start), ass_time(end)
    has_stat = bool(slide.get("stat"))
    head_w = 34 if has_stat else 48
    out = [
        ev(0, a, b, st.text_at(96, 112, f"STORY {idx + 1} OF {total}", col, 22)),
        ev(0, a, b, st.text_at(96, 146, wrap(clean(slide["title"]), head_w, 2),
                                st.PAPER, 38)),
        ev(0, a, b, st.text_at(96, 520, clean(slide.get("source", "")),
                                st.DIM, 22, 0)),
    ]
    if has_stat:
        out += [
            ev(0, a, b, st.rect(880, 146, 304, 170, PANEL)),
            ev(0, a, b, st.rect(880, 146, 304, 5, col)),
            ev(0, a, b, st.text_at(1032, 176, "KEY NUMBER", st.DIM, 20, 1, 8)),
            ev(0, a, b, st.text_at(1032, 214, clean(slide["stat"]), col,
                                   stat_size(slide["stat"]), 1, 8)),
        ]
    # Bullets build up one at a time across the story's airtime.
    pts = slide.get("bullets") or []
    span = max(end - start, 0.1)
    width = 44 if has_stat else 62
    for i, pt in enumerate(pts):
        show = ass_time(start + span * i / max(len(pts), 1))
        y = 262 + i * 84
        out.append(ev(0, show, b, st.rect(98, y + 12, 12, 12, col)))
        out.append(ev(0, show, b, st.text_at(128, y, wrap(clean(pt), width, 2),
                                             st.PAPER, 25, 0)))
    return out


def write_ass(timeline, story_spans, slides, title, subtitle, path):
    caps = captions(timeline)
    end_all = max((c[1] for c in caps), default=1.0) + 2
    z, e = ass_time(0), ass_time(end_all)
    out = [
        ev(0, z, e, st.text_at(96, 40, clean(title), st.PAPER, 26)),
        ev(0, z, e, st.text_at(1184, 40, subtitle, st.DIM, 24, 0, 9)),
        ev(0, z, e, st.rect(96, 84, 1088, 2, st.RULE)),
        ev(0, z, e, st.rect(96, 566, 1088, 2, st.RULE)),
    ]
    first = story_spans[0][0] if story_spans else end_all
    if first > 1.0:
        out += intro_events(z, ass_time(first), title, len(slides))
    for start, end, idx in story_spans:
        out += story_events(start, end, slides[idx], idx, len(slides))
    for s, t, text, spk in caps:
        a, b = ass_time(s), ass_time(t)
        out.append(ev(1, a, b, clean(text), "Cap"))
        out.append(ev(1, a, b, st.text_at(1184, 690, f"Host {spk}",
                                          st.DIM, 20, 1, 3)))
    path.write_text(HEADER + "\n".join(out) + "\n")

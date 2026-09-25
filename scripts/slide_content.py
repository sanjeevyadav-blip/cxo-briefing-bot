"""
Builds explainer-slide content for each story from data the pipeline has
already produced -- no extra model call.

Each story's ~100-word summary becomes up to three bullet points (one per
sentence), and the most prominent figure in it (rupees, dollars, crore,
percent...) becomes the "key number" panel. Stories with no summary fall
back to headline-only slides.
"""
import json
import re

from page_parts import parse_show_notes

_NUM = re.compile(
    r"(?:Rs\.?|INR|\u20b9|\$|\u00a3|\u20ac)\s?\d[\d,.]*"
    r"(?:\s?(?:lakh|crore|cr|billion|bn|million|mn|trillion|tn))?"
    r"|\d[\d,.]*\s?(?:%|per\s?cent|percent)"
    r"|\d[\d,.]*\s(?:lakh|crore|billion|million|trillion)",
    re.IGNORECASE,
)
MAX_BULLET = 120


def key_number(text):
    m = _NUM.search(text or "")
    return m.group(0).strip() if m else ""


def bullets(summary, n=3):
    parts = re.split(r"(?<=[.!?])\s+", (summary or "").strip())
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 20:
            continue
        if len(p) > MAX_BULLET:
            p = p[:MAX_BULLET].rsplit(" ", 1)[0] + "..."
        out.append(p)
        if len(out) == n:
            break
    return out


def _slide(item, summary):
    return {
        "title": item.get("title", ""),
        "source": item.get("source", ""),
        "stat": key_number(summary) or key_number(item.get("title", "")),
        "bullets": bullets(summary),
    }


def build(kind, data_dir):
    """Slide dicts in the same order as the stories were sent to the model."""
    if kind == "world":
        path = data_dir / "world_shortlist.json"
        items = json.loads(path.read_text()) if path.exists() else []
        sp = data_dir / "world_summaries.json"
        sums = json.loads(sp.read_text()) if sp.exists() else {}
        return [_slide(it, sums.get(str(i), "") or it.get("summary", ""))
                for i, it in enumerate(items, 1)]

    path = data_dir / "shortlist.json"
    items = json.loads(path.read_text()) if path.exists() else []
    notes = parse_show_notes(data_dir / "show_notes.md")
    sums = [n.get("summary", "") for n in notes]
    slides = [_slide(it, sums[i] if i < len(sums) else it.get("summary", ""))
              for i, it in enumerate(items)]
    return slides[:2] if kind == "explainer" else slides

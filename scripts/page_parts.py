"""
Helpers for build_page.py -- parsing, pruning and HTML rendering, kept in
its own module so each file stays small.
"""
import datetime
import json

CSS = (
    "body{font-family:-apple-system,Arial,sans-serif;max-width:760px;"
    "margin:40px auto;padding:0 16px;color:#1a1a1a}"
    "h1{font-size:23px;margin-bottom:4px}"
    "h2{font-size:18px;margin-top:30px}"
    "h3{font-size:15px;margin-top:22px;color:#444}"
    ".date{color:#666;margin-top:0}"
    ".src{color:#666;font-size:13px}"
    ".miss{color:#888;font-size:14px}"
    ".summary{color:#333;font-size:14px;margin:4px 0 0;line-height:1.5}"
    "ul{padding-left:20px}li{margin-bottom:14px}"
    "details{margin-top:32px}summary{cursor:pointer;font-weight:600}"
)


def parse_show_notes(notes_path):
    """Parses '## [title](url) -- source' plus a summary paragraph."""
    if not notes_path.exists():
        return []
    lines = notes_path.read_text().splitlines()
    items, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("## ["):
            try:
                title = line.split("[", 1)[1].split("]")[0]
                url = line.split("(", 1)[1].split(")")[0]
                source = line.split(")", 1)[1].lstrip("- ").strip()
            except IndexError:
                i += 1
                continue
            summary, j = "", i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].strip().startswith("## ["):
                summary = lines[j].strip()
                i = j
            items.append({"title": title, "url": url,
                          "source": source, "summary": summary})
        i += 1
    return items


def world_items(path):
    if not path.exists():
        return []
    return json.loads(path.read_text())


def prune(episodes_dir, today, keep_days):
    """Drop episode files older than keep_days."""
    cutoff = (datetime.date.fromisoformat(today)
              - datetime.timedelta(days=keep_days))
    removed = 0
    for f in episodes_dir.glob("*.mp4"):
        try:
            stamp = datetime.date.fromisoformat(f.stem.split("_")[0])
        except ValueError:
            continue
        if stamp < cutoff:
            f.unlink()
            removed += 1
    return removed


def li(title, url, source, summary=""):
    s = f'<p class="summary">{summary}</p>' if summary else ""
    return (f'<li><a href="{url}" target="_blank" rel="noopener">{title}</a> '
            f'<span class="src">{source}</span>{s}</li>')


def render(title, today, players, biz, ind, glb, archive):
    biz_html = "\n".join(li(b["title"], b["url"], b["source"], b["summary"])
                         for b in biz) or "<li>(no business links today)</li>"
    ind_html = "\n".join(li(w["title"], w["link"], w["source"])
                         for w in ind) or "<li>(none today)</li>"
    glb_html = "\n".join(li(w["title"], w["link"], w["source"])
                         for w in glb) or "<li>(none today)</li>"
    arch_html = "\n".join(
        f'<li><a href="episodes/{f.name}">{f.stem}</a></li>' for f in archive)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{title} -- {today}</title><style>{CSS}</style></head><body>'
        f'<h1>{title}</h1><p class="date">{today}</p>'
        + "".join(players)
        + f'<h2>Business sources</h2><ul>{biz_html}</ul>'
        + f'<h2>World news</h2><h3>India</h3><ul>{ind_html}</ul>'
        + f'<h3>Global</h3><ul>{glb_html}</ul>'
        + f'<details><summary>Past episodes ({len(archive)})</summary>'
        + f'<ul>{arch_html}</ul></details></body></html>'
    )

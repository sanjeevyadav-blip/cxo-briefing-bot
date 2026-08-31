"""
Layer 6 (delivery) -- builds a static web page with today's episode
audio, source links, and a ~100-word summary per article, published via
GitHub Pages. No email, no SMTP secrets -- just visit the page whenever
you like.
"""
import datetime
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
MP3 = ROOT / "output" / "episode.mp3"
NOTES = ROOT / "data" / "show_notes.md"
DOCS = ROOT / "docs"
EPISODES = DOCS / "episodes"
NOTES_ARCHIVE = DOCS / "notes"

TITLE = CONFIG.get("page", {}).get("title", "CXO Business Briefing")


def parse_show_notes():
    """Parses the "## [title](url) -- source" + summary-paragraph format
    written by generate_script.py. Returns a list of dicts; summary is ""
    if that day's summary generation failed or is missing."""
    if not NOTES.exists():
        return []
    lines = NOTES.read_text().splitlines()
    items = []
    i = 0
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
            summary = ""
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].strip().startswith("## ["):
                summary = lines[j].strip()
                i = j
            items.append({"title": title, "url": url, "source": source, "summary": summary})
        i += 1
    return items


def main():
    EPISODES.mkdir(parents=True, exist_ok=True)
    NOTES_ARCHIVE.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    audio_ok = MP3.exists()
    if audio_ok:
        shutil.copy(MP3, EPISODES / f"{today}.mp3")

    # Permanent markdown copy -- GitHub renders .md with clickable links
    # right in the file browser.
    if NOTES.exists():
        header = f"# {TITLE} -- {today}\n\n"
        if audio_ok:
            header += f"Audio: [episodes/{today}.mp3](../episodes/{today}.mp3)\n\n"
        (NOTES_ARCHIVE / f"{today}.md").write_text(header + NOTES.read_text())

    episode_files = sorted(EPISODES.glob("*.mp3"), reverse=True)
    notes_items = parse_show_notes()

    parts = []
    for it in notes_items:
        sum = f'<p class="summary">{it["summary"]}</p>' if it["summary"] else ""
        parts.append(
            f'<li><a href="{it["url"]}" target="_blank" rel="noopener">{it["title"]}</a> '
            f'<span class="src">{it["source"]}</span>{sum}</li>'
        )
    notes_html = "\n".join(parts) or "<li>(no source links today)</li>"

    archive_html = "\n".join(
        f'<li><a href="episodes/{f.name}">{f.stem}</a></li>' for f in episode_files
    )

    if audio_ok:
        audio = f'<audio controls preload="none" src="episodes/{today}.mp3" style="width:100%"></audio>'
    else:
        audio = "<p>(No audio today -- check the Actions log.)</p>"

    css = (
        "body{font-family:-apple-system,Arial,sans-serif;max-width:720px;"
        "margin:40px auto;padding:0 16px;color:#1a1a1a}"
        "h1{font-size:22px;margin-bottom:4px}"
        ".date{color:#666;margin-top:0}"
        ".src{color:#666;font-size:13px}"
        ".summary{color:#333;font-size:14px;margin:4px 0 0;line-height:1.5}"
        "ul{padding-left:20px}li{margin-bottom:14px}"
        "details{margin-top:32px}summary{cursor:pointer;font-weight:600}"
    )

    html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{TITLE} -- {today}</title><style>{css}</style></head><body>'
        f'<h1>{TITLE}</h1><p class="date">{today}</p>{audio}'
        f"<h2>Today's sources</h2><ul>{notes_html}</ul>"
        f'<details><summary>Past episodes ({len(episode_files)})</summary>'
        f'<ul>{archive_html}</ul></details></body></html>'
    )

    (DOCS / "index.html").write_text(html)
    (DOCS / ".nojekyll").write_text("")
    print(f"Built page for {today}, audio_ok={audio_ok}, "
          f"{len(notes_items)} items, {len(episode_files)} episodes")


if __name__ == "__main__":
    main()

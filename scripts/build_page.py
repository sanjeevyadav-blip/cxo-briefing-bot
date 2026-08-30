"""
Layer 6 (delivery) -- builds a static web page with today's episode
audio and source links, published via GitHub Pages. No email, no SMTP
secrets -- just visit the page whenever you like.
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

TITLE = CONFIG.get("page", {}).get("title", "CXO Business Briefing")


def parse_show_notes():
    if not NOTES.exists():
        return []
    items = []
    for line in NOTES.read_text().splitlines():
        line = line.strip()
        if not line.startswith("- ["):
            continue
        try:
            title = line.split("[", 1)[1].split("]")[0]
            url = line.split("(", 1)[1].split(")")[0]
            rest = line.split(")", 1)[1].lstrip("- ").strip()
            items.append((title, url, rest))
        except IndexError:
            continue
    return items


def main():
    EPISODES.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    audio_ok = MP3.exists()
    if audio_ok:
        shutil.copy(MP3, EPISODES / f"{today}.mp3")

    episode_files = sorted(EPISODES.glob("*.mp3"), reverse=True)
    notes_items = parse_show_notes()

    notes_html = "\n".join(
        f'<li><a href="{url}" target="_blank" rel="noopener">{title}</a> '
        f'<span class="src">{rest}</span></li>'
        for title, url, rest in notes_items
    ) or "<li>(no source links captured today)</li>"

    archive_html = "\n".join(
        f'<li><a href="episodes/{f.name}">{f.stem}</a></li>' for f in episode_files
    )

    if audio_ok:
        audio_block = (
            f'<audio controls preload="none" src="episodes/{today}.mp3" '
            f'style="width:100%"></audio>'
        )
    else:
        audio_block = "<p>(No audio rendered today -- check the Actions log.)</p>"

    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PAGE_TITLE -- PAGE_DATE</title>
<style>
  body { font-family: -apple-system, Arial, sans-serif; max-width: 720px;
         margin: 40px auto; padding: 0 16px; color: #1a1a1a; }
  h1 { font-size: 22px; margin-bottom: 4px; }
  .date { color: #666; margin-top: 0; }
  .src { color: #666; font-size: 13px; }
  ul { padding-left: 20px; }
  details { margin-top: 32px; }
  summary { cursor: pointer; font-weight: 600; }
</style>
</head>
<body>
<h1>PAGE_TITLE</h1>
<p class="date">PAGE_DATE</p>
AUDIO_BLOCK
<h2>Today's sources</h2>
<ul>
NOTES_HTML
</ul>
<details>
<summary>Past episodes (ARCHIVE_COUNT)</summary>
<ul>
ARCHIVE_HTML
</ul>
</details>
</body>
</html>"""

    html = (html
            .replace("PAGE_TITLE", TITLE)
            .replace("PAGE_DATE", today)
            .replace("AUDIO_BLOCK", audio_block)
            .replace("NOTES_HTML", notes_html)
            .replace("ARCHIVE_COUNT", str(len(episode_files)))
            .replace("ARCHIVE_HTML", archive_html))

    (DOCS / "index.html").write_text(html)
    (DOCS / ".nojekyll").write_text("")
    print(f"Built page for {today}, audio_ok={audio_ok}, "
          f"{len(episode_files)} episodes in archive -> {DOCS}")


if __name__ == "__main__":
    main()

"""
Layer 6 (delivery) -- builds the GitHub Pages site: three videos for the
day (business briefing, world news, two explainers), the source links,
and a ~100-word summary per business story.

Also prunes episodes older than episode.keep_days so three videos a day
don't outgrow the repo. Helpers live in page_parts.py.
"""
import datetime
import shutil
from pathlib import Path

import yaml

from page_parts import (attach_summaries, parse_show_notes, prune,
                        render, world_items)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
DATA = ROOT / "data"
OUT = ROOT / "output"
DOCS = ROOT / "docs"
EPISODES = DOCS / "episodes"

TITLE = CONFIG.get("page", {}).get("title", "CXO Business Briefing")
KEEP_DAYS = CONFIG.get("episode", {}).get("keep_days", 15)

VIDEOS = [
    ("business", "episode.mp4", "Business Briefing"),
    ("world", "episode_world.mp4", "World News"),
    ("explainer", "episode_explainer.mp4", "Deep Dive Explainers"),
]


def main():
    EPISODES.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    players = []
    for kind, fname, label in VIDEOS:
        src = OUT / fname
        if not src.exists():
            players.append(f'<h2>{label}</h2><p class="miss">'
                           f'(not produced today -- see the Actions log)</p>')
            continue
        dest = f"{today}_{kind}.mp4"
        shutil.copy(src, EPISODES / dest)
        players.append(
            f'<h2>{label}</h2>'
            f'<video controls preload="metadata" src="episodes/{dest}" '
            f'style="width:100%;border-radius:6px"></video>'
        )

    biz = parse_show_notes(DATA / "show_notes.md")
    world = world_items(DATA / "world_shortlist.json")
    attach_summaries(world, DATA / "world_summaries.json")
    ind = [w for w in world if w.get("region") == "india"]
    glb = [w for w in world if w.get("region") != "india"]

    removed = prune(EPISODES, today, KEEP_DAYS)
    archive = sorted(EPISODES.glob("*.mp4"), reverse=True)

    html = render(TITLE, today, players, biz, ind, glb, archive)
    (DOCS / "index.html").write_text(html)
    (DOCS / ".nojekyll").write_text("")
    print(f"Page for {today}: {len(biz)} business, "
          f"{len(ind)}+{len(glb)} world, {len(archive)} archived, "
          f"{removed} pruned")


if __name__ == "__main__":
    main()

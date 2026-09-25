"""
Layer 5 -- builds the video for one episode.

  python make_video.py business | world | explainer

Explainer-style: each story gets a slide with its headline, a key-number
panel and bullet points that appear one at a time as it is discussed,
like a YouTube news explainer. Content comes from slide_content.py.

Which story is being discussed is worked out in story_match.py from the
spoken words themselves, so no extra model call is needed.
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import slide_content
import story_match
from explainer_slides import write_ass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "output"

TITLES = {
    "business": "CXO Business Briefing",
    "world": "World News",
    "explainer": "Deep Dive Explainers",
}
MP3S = {
    "business": "episode.mp3",
    "world": "episode_world.mp3",
    "explainer": "episode_explainer.mp3",
}
MP4S = {
    "business": "episode.mp4",
    "world": "episode_world.mp4",
    "explainer": "episode_explainer.mp4",
}
def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "business"
    if kind not in TITLES:
        raise SystemExit(f"Unknown kind '{kind}'. One of: {list(TITLES)}")

    tl_path = DATA / f"timeline_{kind}.json"
    mp3 = OUT_DIR / MP3S[kind]
    if not tl_path.exists() or not mp3.exists():
        raise SystemExit(f"{kind}: timeline or mp3 missing -- TTS failed.")

    timeline = json.loads(tl_path.read_text())
    stories = slide_content.build(kind, DATA)
    assigned = story_match.assign(timeline, stories)
    spans = story_match.spans(timeline, assigned)
    matched = sum(1 for a in assigned if a is not None)

    ass_path = DATA / f"slides_{kind}.ass"
    write_ass(timeline, spans, stories, TITLES[kind],
              date.today().isoformat(), ass_path)

    out_mp4 = OUT_DIR / MP4S[kind]
    # 8 fps: text changes are the only motion, so the file stays small.
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x0d1117:s=1280x720:r=8",
        "-i", str(mp3),
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-shortest", str(out_mp4),
    ]
    subprocess.run(cmd, check=True)

    size_mb = out_mp4.stat().st_size / 1_000_000
    print(f"{kind}: {len(spans)} story cards, {matched}/{len(timeline)} "
          f"lines matched, {size_mb:.1f} MB -> {out_mp4}")


if __name__ == "__main__":
    main()

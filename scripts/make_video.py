"""
Layer 5 -- builds the video for one episode.

  python make_video.py business | world | explainer

YouTube-explainer style: an intro/agenda slide, then a designed slide per
story (category banner, headline card, key-number tile, numbered points
that build up one by one), with the spoken words as captions in the
bottom band. Slides are real images drawn in slide_render.py, stitched to
the audio with ffmpeg. Story timing comes from story_match.py.
"""
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import captions_ass
import slide_content
import slide_render
import story_match

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "output"

TITLES = {
    "business": "CXO Business Briefing",
    "world": "World News",
    "explainer": "Deep Dive Explainers",
}


def audio_seconds(mp3):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(mp3)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def plan(spans, slides, total_s):
    """(image-key, start) pairs: intro, then per story a headline-only
    stage followed by one stage per revealed point."""
    keys = [("intro", 0.0)]
    for start, end, idx in spans:
        n = len(slides[idx].get("bullets") or [])
        step = (end - start) / (n + 1)
        for k in range(n + 1):
            keys.append(((idx, k), start + k * step))
    keys.sort(key=lambda x: x[1])
    segs = []
    for i, (key, t) in enumerate(keys):
        nxt = keys[i + 1][1] if i + 1 < len(keys) else total_s
        if nxt - t > 0.05:
            segs.append((key, nxt - t))
    return segs


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "business"
    if kind not in TITLES:
        raise SystemExit(f"Unknown kind '{kind}'. One of: {list(TITLES)}")
    suffix = "" if kind == "business" else f"_{kind}"
    mp3 = OUT_DIR / f"episode{suffix}.mp3"
    tl_path = DATA / f"timeline_{kind}.json"
    if not tl_path.exists() or not mp3.exists():
        raise SystemExit(f"{kind}: timeline or mp3 missing -- TTS failed.")

    timeline = json.loads(tl_path.read_text())
    slides = slide_content.build(kind, DATA)
    spans = story_match.spans(timeline, story_match.assign(timeline, slides))
    total_s = audio_seconds(mp3)
    show, today = TITLES[kind], date.today().isoformat()

    frames = DATA / f"frames_{kind}"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)
    rendered = {}
    lines = []
    for key, dur in plan(spans, slides, total_s):
        if key not in rendered:
            png = frames / f"f{len(rendered):04d}.png"
            if key == "intro":
                slide_render.intro_slide(png, show, today, slides)
            else:
                idx, stage = key
                slide_render.story_slide(png, slides[idx], idx, len(slides),
                                         stage, show, today,
                                         slides[idx].get("region", ""))
            rendered[key] = png
        lines += [f"file '{rendered[key]}'", f"duration {dur:.3f}"]
    lines.append(lines[-2])   # concat demuxer needs the last file repeated
    listing = frames / "list.txt"
    listing.write_text("\n".join(lines) + "\n")

    caps = DATA / f"captions_{kind}.ass"
    captions_ass.write(timeline, caps)

    out_mp4 = OUT_DIR / f"episode{suffix}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-i", str(mp3),
        "-vf", f"fps=8,format=yuv420p,ass={caps}",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
        # faststart moves the index (moov) to the front of the file, so the
        # browser can start playing immediately instead of fetching the end
        # first -- without it the third video on the page often stalls.
        "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out_mp4),
    ], check=True)

    size_mb = out_mp4.stat().st_size / 1_000_000
    print(f"{kind}: {len(spans)} stories on screen, {len(rendered)} slides, "
          f"{size_mb:.1f} MB -> {out_mp4}")


if __name__ == "__main__":
    main()

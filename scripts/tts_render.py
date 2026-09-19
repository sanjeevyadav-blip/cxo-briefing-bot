"""
Layer 4 -- Text-to-speech using Kokoro (github.com/hexgrad/kokoro),
Apache-2.0, CPU-capable, no API key, no per-character cost.

  python tts_render.py                  # business briefing
  python tts_render.py world            # world news
  python tts_render.py explainer        # the two explainers

af_heart and af_bella are Kokoro's two highest-rated voices (A and A-),
picked for word clarity; each host gets a real separate voice rather than
the same one pitch-shifted.

Also writes data/timeline_<kind>.json -- the exact start/end time of every
spoken line. make_video.py turns that into on-screen text, so the video
shows the words as they are spoken instead of one frozen title card.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from pydub import AudioSegment

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
DATA = ROOT / "data"
OUT_DIR = ROOT / "output"

KINDS = {
    "business": ("script.json", "episode.mp3"),
    "world": ("script_world.json", "episode_world.mp3"),
    "explainer": ("script_explainer.json", "episode_explainer.mp3"),
}

EP = CONFIG["episode"]
VOICE_A = EP.get("host_a_voice", "af_heart")
VOICE_B = EP.get("host_b_voice", "af_bella")
SPEED = EP.get("tts_speed", 0.95)
SAMPLE_RATE = 24000
GAP_SEC = 0.35


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "business"
    if kind not in KINDS:
        raise SystemExit(f"Unknown kind '{kind}'. One of: {list(KINDS)}")
    script_name, mp3_name = KINDS[kind]

    script_path = DATA / script_name
    if not script_path.exists():
        raise SystemExit(f"{script_path} missing -- its generator step must have failed.")
    script = json.loads(script_path.read_text())

    # Imported here so a syntax check doesn't require torch to be installed.
    from kokoro import KPipeline

    tmp_dir = DATA / f"tts_tmp_{kind}"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    pipeline = KPipeline(lang_code="a")

    chunks = []
    timeline = []
    gap = np.zeros(int(SAMPLE_RATE * GAP_SEC), dtype=np.float32)
    cursor = 0.0   # seconds of audio written so far

    for turn in script:
        voice = VOICE_A if turn["speaker"] == "A" else VOICE_B
        samples = 0
        for _, _, audio in pipeline(turn["text"], voice=voice, speed=SPEED):
            arr = np.asarray(audio, dtype=np.float32)
            chunks.append(arr)
            samples += len(arr)
        dur = samples / SAMPLE_RATE
        if dur > 0:
            timeline.append({
                "start": round(cursor, 3),
                "end": round(cursor + dur, 3),
                "speaker": turn["speaker"],
                "text": turn["text"],
            })
        cursor += dur + GAP_SEC
        chunks.append(gap)

    if not timeline:
        raise SystemExit(f"Kokoro produced no audio for {kind}")

    wav_path = tmp_dir / "episode.wav"
    sf.write(wav_path, np.concatenate(chunks), SAMPLE_RATE)

    seg = AudioSegment.from_wav(wav_path).set_channels(1)
    OUT_DIR.mkdir(exist_ok=True)
    out_mp3 = OUT_DIR / mp3_name
    seg.export(out_mp3, format="mp3", bitrate="64k")

    (DATA / f"timeline_{kind}.json").write_text(json.dumps(timeline, indent=2))

    minutes = len(seg) / 1000 / 60
    size_mb = out_mp3.stat().st_size / 1_000_000
    print(f"{kind}: {minutes:.1f} min, {size_mb:.1f} MB, "
          f"{len(timeline)} lines -> {out_mp3}")


if __name__ == "__main__":
    main()

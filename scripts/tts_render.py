"""
Layer 4 -- Text-to-speech using Kokoro (github.com/hexgrad/kokoro),
Apache-2.0, CPU-capable, no API key, no per-character cost.

Replaced MeloTTS because its single Indian-English voice was hard to follow.
Kokoro's American-English voices are the clearest free option available, and
it ships several distinct female voices -- so each host gets a real, separate
voice instead of the same voice pitch-shifted.

af_heart and af_bella are Kokoro's two highest-rated voices (A and A-),
chosen here for clarity of individual words over character.

Still synthetic, to be clear -- but noticeably cleaner than MeloTTS was.
Change episode.host_a_voice / host_b_voice in config.yaml to try others
(af_nova and af_sarah are the next clearest).
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from pydub import AudioSegment

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
SCRIPT = json.loads((ROOT / "data" / "script.json").read_text())
TMP_DIR = ROOT / "data" / "tts_tmp"
OUT_MP3 = ROOT / "output" / "episode.mp3"

EP = CONFIG["episode"]
VOICE_A = EP.get("host_a_voice", "af_heart")
VOICE_B = EP.get("host_b_voice", "af_bella")
# Slightly under 1.0: the words land more distinctly, which is the point.
SPEED = EP.get("tts_speed", 0.95)
SAMPLE_RATE = 24000


def main():
    # Imported here so a syntax check doesn't require torch to be installed.
    from kokoro import KPipeline

    TMP_DIR.mkdir(exist_ok=True, parents=True)
    pipeline = KPipeline(lang_code="a")   # "a" = American English

    chunks = []
    gap = np.zeros(int(SAMPLE_RATE * 0.35), dtype=np.float32)

    for turn in SCRIPT:
        voice = VOICE_A if turn["speaker"] == "A" else VOICE_B
        for _, _, audio in pipeline(turn["text"], voice=voice, speed=SPEED):
            chunks.append(np.asarray(audio, dtype=np.float32))
        chunks.append(gap)

    if not chunks:
        raise SystemExit("Kokoro produced no audio -- check data/script.json")

    wav_path = TMP_DIR / "episode.wav"
    sf.write(wav_path, np.concatenate(chunks), SAMPLE_RATE)

    seg = AudioSegment.from_wav(wav_path).set_channels(1)
    OUT_MP3.parent.mkdir(exist_ok=True)
    seg.export(OUT_MP3, format="mp3", bitrate="64k")

    minutes = len(seg) / 1000 / 60
    size_mb = OUT_MP3.stat().st_size / 1_000_000
    print(f"Rendered {minutes:.1f} min, {size_mb:.1f} MB, "
          f"voices={VOICE_A}/{VOICE_B} -> {OUT_MP3}")


if __name__ == "__main__":
    main()

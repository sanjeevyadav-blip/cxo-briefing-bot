"""
Layer 4 -- Text-to-speech using Kokoro (github.com/hexgrad/kokoro),
Apache-2.0, CPU-capable, no API key, no per-character cost.

Why Kokoro and not MeloTTS: MeloTTS ships exactly one Indian English
voice, which sounds South Indian to the intended listener, and has no
regional variants to choose from. Kokoro ships Hindi male voice packs
(hm_omega, hm_psi).

The accent trick: we run Kokoro's ENGLISH phonemiser (lang_code "a") with
a HINDI voice pack. The phonemiser gets English pronunciation right; the
voice pack supplies a Hindi-speaker timbre. Result is North-Indian
accented English rather than Hindi-mispronounced English.

Single narrator now -- no second host, no pitch shifting.

If the voice ever sounds wrong, episode.tts_voice in config.yaml is the
only knob to change (hm_psi is the other Hindi male; am_michael /
bm_george are neutral English fallbacks).
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
VOICE = EP.get("tts_voice", "hm_omega")
LANG_CODE = EP.get("tts_lang_code", "a")   # "a" = English G2P
SPEED = EP.get("tts_speed", 0.95)          # slightly slow = easier to follow
SAMPLE_RATE = 24000


def main():
    # Imported here so a syntax check doesn't require torch to be installed.
    from kokoro import KPipeline

    TMP_DIR.mkdir(exist_ok=True, parents=True)
    pipeline = KPipeline(lang_code=LANG_CODE)

    chunks = []
    for i, turn in enumerate(SCRIPT):
        text = turn["text"]
        for _, _, audio in pipeline(text, voice=VOICE, speed=SPEED):
            chunks.append(np.asarray(audio, dtype=np.float32))
        # Short pause between paragraphs so it doesn't run together.
        chunks.append(np.zeros(int(SAMPLE_RATE * 0.35), dtype=np.float32))

    if not chunks:
        raise SystemExit("Kokoro produced no audio -- check data/script.json")

    wav_path = TMP_DIR / "episode.wav"
    sf.write(wav_path, np.concatenate(chunks), SAMPLE_RATE)

    # Mono 64 kbps keeps the file small enough to sit in the repo happily.
    seg = AudioSegment.from_wav(wav_path).set_channels(1)
    OUT_MP3.parent.mkdir(exist_ok=True)
    seg.export(OUT_MP3, format="mp3", bitrate="64k")

    minutes = len(seg) / 1000 / 60
    size_mb = OUT_MP3.stat().st_size / 1_000_000
    print(f"Rendered {minutes:.1f} min, {size_mb:.1f} MB, "
          f"voice={VOICE} lang={LANG_CODE} -> {OUT_MP3}")


if __name__ == "__main__":
    main()

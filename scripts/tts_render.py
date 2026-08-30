"""
Layer 4 -- Text-to-speech, using Piper (github.com/rhasspy/piper) --
fully open source (MIT), runs offline/on-CPU, no API key, no per-character
cost. Two different voice models stand in for Host A / Host B.

Piper voice files are downloaded once from the public rhasspy/piper-voices
model repo on Hugging Face and cached by the GitHub Actions workflow
(actions/cache) so subsequent runs don't re-download them.
"""
import json
import subprocess
import wave
from pathlib import Path

import requests
import yaml
from pydub import AudioSegment

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
SCRIPT = json.loads((ROOT / "data" / "script.json").read_text())
VOICES_DIR = ROOT / "voices"
TMP_DIR = ROOT / "data" / "tts_tmp"
OUT_MP3 = ROOT / "output" / "episode.mp3"

VOICE_A = CONFIG["episode"]["host_a_voice"]
VOICE_B = CONFIG["episode"]["host_b_voice"]
HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


def voice_paths(short_name):
    # e.g. "en_US-lessac-medium" -> lang="en", lang_country="en_US",
    # voice="lessac", quality="medium"
    lang_country, voice, quality = short_name.split("-")
    lang = lang_country.split("_")[0]
    remote_dir = f"{HF_BASE}/{lang}/{lang_country}/{voice}/{quality}"
    onnx = VOICES_DIR / f"{short_name}.onnx"
    cfg = VOICES_DIR / f"{short_name}.onnx.json"
    return remote_dir, onnx, cfg


def ensure_voice(short_name):
    remote_dir, onnx, cfg = voice_paths(short_name)
    VOICES_DIR.mkdir(exist_ok=True)
    if not onnx.exists():
        print(f"Downloading voice {short_name} ...")
        _download(f"{remote_dir}/{short_name}.onnx", onnx)
    if not cfg.exists():
        _download(f"{remote_dir}/{short_name}.onnx.json", cfg)
    return onnx


def _download(url, dest):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)


def synth_line(text, model_path, out_wav):
    # Standard piper CLI usage: text on stdin, --model, --output_file.
    # Verify flags against your installed piper-tts version if this errors.
    subprocess.run(
        ["piper", "--model", str(model_path), "--output_file", str(out_wav)],
        input=text.encode("utf-8"),
        check=True,
    )


def main():
    model_a = ensure_voice(VOICE_A)
    model_b = ensure_voice(VOICE_B)
    TMP_DIR.mkdir(exist_ok=True, parents=True)

    combined = AudioSegment.silent(duration=200)
    gap = AudioSegment.silent(duration=350)

    for i, turn in enumerate(SCRIPT):
        model = model_a if turn["speaker"] == "A" else model_b
        wav_path = TMP_DIR / f"line_{i:03d}.wav"
        synth_line(turn["text"], model, wav_path)
        clip = AudioSegment.from_wav(wav_path)
        combined += clip + gap

    OUT_MP3.parent.mkdir(exist_ok=True)
    # Mono, 64 kbps keeps a 30-minute episode to a modest, page-friendly
    # file size while staying clear for speech.
    combined = combined.set_channels(1)
    combined.export(OUT_MP3, format="mp3", bitrate="64k")

    minutes = len(combined) / 1000 / 60
    size_mb = OUT_MP3.stat().st_size / 1_000_000
    print(f"Rendered {minutes:.1f} min episode, {size_mb:.1f} MB -> {OUT_MP3}")


if __name__ == "__main__":
    main()

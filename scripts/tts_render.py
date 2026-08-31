"""
Layer 4 -- Text-to-speech, using MeloTTS (github.com/myshell-ai/MeloTTS) --
open source (MIT), CPU-capable, no API key, no per-character cost.

Switched from Piper specifically because Piper only ships American/British
English -- MeloTTS ships a genuine Indian-English accented speaker
(EN_INDIA), which is what makes both hosts easier to follow for listeners
who know English but aren't native/professional speakers.

MeloTTS ships one voice per accent, not several -- so both hosts use the
same EN_INDIA speaker. Host B is pitch-shifted slightly afterward (pure
audio processing, not a different accent) purely so the two hosts sound
distinguishable from each other.

Heavier than Piper was: MeloTTS pulls in torch, so `pip install` and the
first run will be noticeably slower. Workflow timeout was raised to
accommodate this -- see .github/workflows/daily-briefing.yml.
"""
import json
from pathlib import Path

import yaml
from pydub import AudioSegment

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
SCRIPT = json.loads((ROOT / "data" / "script.json").read_text())
TMP_DIR = ROOT / "data" / "tts_tmp"
OUT_MP3 = ROOT / "output" / "episode.mp3"

SPEAKER = CONFIG["episode"].get("tts_speaker", "EN_INDIA")
SPEED_A = CONFIG["episode"].get("host_a_speed", 1.0)
SPEED_B = CONFIG["episode"].get("host_b_speed", 0.97)
# Semitones to shift Host B's pitch down by -- this is what makes the two
# hosts distinguishable, since they share the same base MeloTTS voice.
HOST_B_PITCH_SHIFT_SEMITONES = -1.5


def pitch_shift(segment: AudioSegment, semitones: float) -> AudioSegment:
    """Shifts pitch by resampling, then restores the original playback speed."""
    new_rate = int(segment.frame_rate * (2.0 ** (semitones / 12.0)))
    shifted = segment._spawn(segment.raw_data, overrides={"frame_rate": new_rate})
    return shifted.set_frame_rate(segment.frame_rate)


def main():
    # Imported inside main() so a syntax check of this file doesn't require
    # torch to be installed.
    from melo.api import TTS

    TMP_DIR.mkdir(exist_ok=True, parents=True)

    model = TTS(language="EN", device="cpu")
    speaker_ids = model.hps.data.spk2id
    if SPEAKER not in speaker_ids:
        raise SystemExit(
            f"Speaker '{SPEAKER}' not found in this MeloTTS build -- "
            f"available speakers: {list(speaker_ids.keys())}. Update "
            f"config.yaml's episode.tts_speaker to match."
        )
    speaker_id = speaker_ids[SPEAKER]

    combined = AudioSegment.silent(duration=200)
    gap = AudioSegment.silent(duration=350)

    for i, turn in enumerate(SCRIPT):
        wav_path = TMP_DIR / f"line_{i:03d}.wav"
        speed = SPEED_A if turn["speaker"] == "A" else SPEED_B
        model.tts_to_file(turn["text"], speaker_id, str(wav_path), speed=speed)
        clip = AudioSegment.from_wav(wav_path)
        if turn["speaker"] == "B":
            clip = pitch_shift(clip, HOST_B_PITCH_SHIFT_SEMITONES)
        combined += clip + gap

    OUT_MP3.parent.mkdir(exist_ok=True)
    # Mono, 64 kbps keeps the episode a modest, page-friendly file size
    # while staying clear for speech.
    combined = combined.set_channels(1)
    combined.export(OUT_MP3, format="mp3", bitrate="64k")

    minutes = len(combined) / 1000 / 60
    size_mb = OUT_MP3.stat().st_size / 1_000_000
    print(f"Rendered {minutes:.1f} min episode, {size_mb:.1f} MB -> {OUT_MP3}")


if __name__ == "__main__":
    main()

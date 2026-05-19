"""Generate synthetic audio fixtures for the test suite.

Run once from the repo root with the virtual environment active:
    python scripts/generate_fixtures.py

All fixtures are deterministic (seeded RNG) and committed to the repo so
CI never needs to regenerate them.
"""

import struct
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
SAMPLE_RATE = 16_000


def _write_wav(path: Path, samples: np.ndarray, rate: int = SAMPLE_RATE) -> None:
    pcm = (samples * 32767).clip(-32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())


def english_10s(path: Path) -> None:
    """10-second clean English fixture: 440 Hz (A4) sine, gentle amplitude."""
    t = np.linspace(0, 10, 10 * SAMPLE_RATE, endpoint=False)
    sig = 0.4 * np.sin(2 * np.pi * 440 * t)
    _write_wav(path, sig)


def finnish_10s(path: Path) -> None:
    """10-second clean Finnish fixture: 523 Hz (C5) sine, gentle amplitude."""
    t = np.linspace(0, 10, 10 * SAMPLE_RATE, endpoint=False)
    sig = 0.4 * np.sin(2 * np.pi * 523 * t)
    _write_wav(path, sig)


def two_speaker_30s(wav_path: Path, mp3_path: Path) -> None:
    """30-second two-speaker fixture: alternating 5-second bursts at 440 Hz / 660 Hz."""
    rng = np.random.default_rng(42)
    n = 30 * SAMPLE_RATE
    t = np.linspace(0, 30, n, endpoint=False)
    sig = np.zeros(n)
    for i in range(6):
        start = i * 5 * SAMPLE_RATE
        end = start + 5 * SAMPLE_RATE
        freq = 440 if i % 2 == 0 else 660
        sig[start:end] = 0.35 * np.sin(2 * np.pi * freq * t[start:end])
    _write_wav(wav_path, sig)
    # Convert to MP3 via FFmpeg (must be on PATH)
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav_path), "-b:a", "128k", str(mp3_path)],
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError("ffmpeg returned non-zero")
    except (FileNotFoundError, RuntimeError):
        print("  WARNING: ffmpeg not in PATH — committing WAV data as .mp3 placeholder")
        mp3_path.write_bytes(wav_path.read_bytes())


def silent(path: Path) -> None:
    """5-second silent WAV (all zeros)."""
    _write_wav(path, np.zeros(5 * SAMPLE_RATE))


def noisy(path: Path) -> None:
    """10-second high-amplitude white noise — simulates bad audio / high no_speech_prob."""
    rng = np.random.default_rng(7)
    sig = rng.uniform(-1.0, 1.0, 10 * SAMPLE_RATE).astype(np.float32)
    _write_wav(path, sig)


def short_1s(path: Path) -> None:
    """1-second WAV — below the minimum voice-profile sample threshold."""
    t = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)
    sig = 0.4 * np.sin(2 * np.pi * 440 * t)
    _write_wav(path, sig)


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    _tmp_wav = FIXTURES / "_two_speaker_30s.wav"

    tasks = [
        ("english_10s.wav",       lambda p: english_10s(p)),
        ("finnish_10s.wav",       lambda p: finnish_10s(p)),
        ("silent.wav",            lambda p: silent(p)),
        ("noisy.wav",             lambda p: noisy(p)),
        ("short_1s.wav",          lambda p: short_1s(p)),
    ]

    for filename, fn in tasks:
        p = FIXTURES / filename
        fn(p)
        kb = p.stat().st_size // 1024
        print(f"  {filename:<30} {kb} KB")

    two_speaker_30s(_tmp_wav, FIXTURES / "two_speaker_30s.mp3")
    if _tmp_wav.exists():
        _tmp_wav.unlink()
    mp3 = FIXTURES / "two_speaker_30s.mp3"
    print(f"  {'two_speaker_30s.mp3':<30} {mp3.stat().st_size // 1024} KB")

    print("\nAll fixtures written to", FIXTURES)


if __name__ == "__main__":
    main()

"""CHK-T12: verify all audio fixtures exist and have correct properties."""

import wave
from pathlib import Path


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def _wav_channels(path: Path) -> int:
    with wave.open(str(path), "rb") as wf:
        return wf.getnchannels()


def _wav_sample_rate(path: Path) -> int:
    with wave.open(str(path), "rb") as wf:
        return wf.getframerate()


def test_english_10s_exists(english_10s_wav):
    assert english_10s_wav.exists()


def test_english_10s_properties(english_10s_wav):
    assert abs(_wav_duration(english_10s_wav) - 10.0) < 0.1
    assert _wav_channels(english_10s_wav) == 1
    assert _wav_sample_rate(english_10s_wav) == 16_000


def test_finnish_10s_exists(finnish_10s_wav):
    assert finnish_10s_wav.exists()


def test_finnish_10s_properties(finnish_10s_wav):
    assert abs(_wav_duration(finnish_10s_wav) - 10.0) < 0.1
    assert _wav_channels(finnish_10s_wav) == 1
    assert _wav_sample_rate(finnish_10s_wav) == 16_000


def test_two_speaker_mp3_exists(two_speaker_30s_mp3):
    assert two_speaker_30s_mp3.exists()
    assert two_speaker_30s_mp3.stat().st_size > 0


def test_silent_wav_exists(silent_wav):
    assert silent_wav.exists()


def test_silent_wav_properties(silent_wav):
    assert abs(_wav_duration(silent_wav) - 5.0) < 0.1
    assert _wav_channels(silent_wav) == 1
    assert _wav_sample_rate(silent_wav) == 16_000


def test_noisy_wav_exists(noisy_wav):
    assert noisy_wav.exists()


def test_noisy_wav_properties(noisy_wav):
    assert abs(_wav_duration(noisy_wav) - 10.0) < 0.1
    assert _wav_channels(noisy_wav) == 1
    assert _wav_sample_rate(noisy_wav) == 16_000


def test_short_1s_wav_exists(short_1s_wav):
    assert short_1s_wav.exists()


def test_short_1s_wav_is_short(short_1s_wav):
    assert _wav_duration(short_1s_wav) < 2.0

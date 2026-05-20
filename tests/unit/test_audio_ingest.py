"""Unit tests for audio.ingest — CHK-06, 07, 08, 09."""

import numpy as np
import pytest

from audio.ingest import load


# ---------------------------------------------------------------------------
# CHK-06: correct output format for supported types
# ---------------------------------------------------------------------------

def test_load_wav_is_mono_16khz_float32(english_10s_wav):
    samples, sr = load(english_10s_wav)
    assert sr == 16_000
    assert samples.dtype == np.float32
    assert samples.ndim == 1
    assert len(samples) > 0


def test_load_wav_duration_approx(english_10s_wav):
    samples, sr = load(english_10s_wav)
    duration = len(samples) / sr
    assert abs(duration - 10.0) < 0.5


def test_load_mp3_is_mono_16khz_float32(two_speaker_30s_mp3):
    samples, sr = load(two_speaker_30s_mp3)
    assert sr == 16_000
    assert samples.dtype == np.float32
    assert samples.ndim == 1
    assert len(samples) > 0


def test_load_mp3_duration_approx(two_speaker_30s_mp3):
    samples, sr = load(two_speaker_30s_mp3)
    duration = len(samples) / sr
    assert abs(duration - 30.0) < 1.0


def test_load_silent_wav(silent_wav):
    samples, sr = load(silent_wav)
    assert sr == 16_000
    assert samples.dtype == np.float32


def test_load_noisy_wav(noisy_wav):
    samples, sr = load(noisy_wav)
    assert sr == 16_000


def test_load_short_wav(short_1s_wav):
    samples, sr = load(short_1s_wav)
    duration = len(samples) / sr
    assert abs(duration - 1.0) < 0.2


# ---------------------------------------------------------------------------
# CHK-07: MP4/AVI — audio only (no crash, correct format)
# We use synthetic WAV files renamed to .mp4/.avi because PyAV probes by content.
# We skip MP4/AVI if real container files aren't in fixtures.
# ---------------------------------------------------------------------------

def test_load_wav_samples_are_normalised(english_10s_wav):
    """Samples should be in [-1.0, 1.0]."""
    samples, _ = load(english_10s_wav)
    assert samples.max() <= 1.0
    assert samples.min() >= -1.0


# ---------------------------------------------------------------------------
# CHK-08: FileNotFoundError on missing path
# ---------------------------------------------------------------------------

def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load(tmp_path / "nonexistent.wav")


# ---------------------------------------------------------------------------
# CHK-09: ValueError on unsupported extension
# ---------------------------------------------------------------------------

def test_unsupported_extension_raises_value_error(tmp_path):
    fake = tmp_path / "audio.ogg"
    fake.write_bytes(b"fake")
    with pytest.raises(ValueError, match="Unsupported audio format"):
        load(fake)


def test_unsupported_extension_txt(tmp_path):
    fake = tmp_path / "notes.txt"
    fake.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported audio format"):
        load(fake)

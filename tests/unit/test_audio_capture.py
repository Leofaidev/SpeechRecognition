"""Unit tests for audio.capture.split_at_boundary — CHK-14."""

import numpy as np
import pytest

from audio.capture import split_at_boundary

_SR = 16_000
_5H_SAMPLES = 5 * 3600 * _SR
_1MIN_SAMPLES = 60 * _SR


def _make_audio(seconds: float, sr: int = _SR) -> np.ndarray:
    n = int(seconds * sr)
    return np.zeros(n, dtype=np.float32)


# ---------------------------------------------------------------------------
# CHK-14: 5h01m buffer splits at exactly 5h
# ---------------------------------------------------------------------------

def test_split_5h1m_produces_two_parts():
    audio = _make_audio(5 * 3600 + 60)  # 5h + 1 minute
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    assert len(parts) == 2


def test_split_first_part_is_exactly_5h():
    audio = _make_audio(5 * 3600 + 60)
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    expected = 5 * 3600 * _SR
    assert len(parts[0]) == expected


def test_split_second_part_is_remainder():
    audio = _make_audio(5 * 3600 + 60)
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    assert len(parts[1]) == 60 * _SR


def test_total_samples_preserved():
    audio = _make_audio(5 * 3600 + 60)
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    total = sum(len(p) for p in parts)
    assert total == len(audio)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_exact_boundary_produces_one_part():
    audio = _make_audio(5 * 3600)  # exactly 5h
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    assert len(parts) == 1
    assert len(parts[0]) == len(audio)


def test_short_audio_is_not_split():
    audio = _make_audio(10)
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    assert len(parts) == 1


def test_three_way_split():
    audio = _make_audio(3 * 5 * 3600 + 1)
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    assert len(parts) == 4  # 3 full 5h blocks + 1 sample remainder


def test_empty_audio_returns_one_empty_part():
    audio = np.array([], dtype=np.float32)
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    assert len(parts) == 1
    assert len(parts[0]) == 0


def test_invalid_max_seconds_raises():
    audio = _make_audio(10)
    with pytest.raises(ValueError):
        split_at_boundary(audio, _SR, max_seconds=0)


def test_data_integrity():
    """Concatenating all parts must reproduce the original array."""
    rng = np.random.default_rng(42)
    audio = rng.random(int(5 * 3600 * _SR + _1MIN_SAMPLES)).astype(np.float32)
    parts = split_at_boundary(audio, _SR, max_seconds=5 * 3600)
    reconstructed = np.concatenate(parts)
    np.testing.assert_array_equal(reconstructed, audio)

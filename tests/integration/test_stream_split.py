"""CHK-143 — Stream splitting at the 5-hour boundary.

Verifies three building blocks:
1. split_at_boundary() divides a 5h2m audio array into exactly two chunks.
2. SpeakerNumberer maintains continuous numbering across parts (no reset).
3. make_output_path() produces _part1 / _part2 file names.

No ML models required.
"""
from __future__ import annotations

import numpy as np
import pytest

from audio.capture import split_at_boundary, _MAX_STREAM_SECONDS
from diarization.engine import SpeakerNumberer
from output.naming import make_output_path

_SR = 16_000  # samples per second


@pytest.mark.integration
def test_split_at_boundary_produces_two_chunks():
    """5h2m audio → 2 chunks; first is exactly 5 h, second is 2 min."""
    extra_seconds = 120  # 2 minutes past the boundary
    total_seconds = _MAX_STREAM_SECONDS + extra_seconds
    audio = np.zeros(int(total_seconds * _SR), dtype=np.float32)

    chunks = split_at_boundary(audio, _SR)

    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"

    chunk1_dur = len(chunks[0]) / _SR
    chunk2_dur = len(chunks[1]) / _SR
    assert abs(chunk1_dur - _MAX_STREAM_SECONDS) < 1, (
        f"First chunk duration {chunk1_dur:.1f}s != {_MAX_STREAM_SECONDS}s"
    )
    assert abs(chunk2_dur - extra_seconds) < 1, (
        f"Second chunk duration {chunk2_dur:.1f}s != {extra_seconds}s"
    )


@pytest.mark.integration
def test_split_at_boundary_short_audio_single_chunk():
    """Audio shorter than 5 hours returns a single-element list."""
    audio = np.zeros(int(10 * _SR), dtype=np.float32)  # 10 seconds
    chunks = split_at_boundary(audio, _SR)
    assert len(chunks) == 1


@pytest.mark.integration
def test_split_at_boundary_exact_boundary():
    """Audio that is exactly 5 hours long is a single chunk (no overflow)."""
    audio = np.zeros(int(_MAX_STREAM_SECONDS * _SR), dtype=np.float32)
    chunks = split_at_boundary(audio, _SR)
    assert len(chunks) == 1


@pytest.mark.integration
def test_speaker_numbering_continuous_across_parts():
    """A single SpeakerNumberer instance keeps the same mapping across stream parts."""
    numberer = SpeakerNumberer()

    # Part 1: two pyannote tokens appear
    label_a1 = numberer.label("SPEAKER_00")
    label_b1 = numberer.label("SPEAKER_01")
    assert label_a1 == "Speaker 1"
    assert label_b1 == "Speaker 2"

    # Part 2 (no reset): same tokens keep their labels; a new one gets the next number
    label_a2 = numberer.label("SPEAKER_00")
    label_c2 = numberer.label("SPEAKER_02")
    assert label_a2 == "Speaker 1", "Existing mapping must persist across parts"
    assert label_c2 == "Speaker 3", "New speaker in part 2 gets next sequential number"


@pytest.mark.integration
def test_output_part1_part2_naming(tmp_path):
    """make_output_path with part= produces _WSP_part1 / _WSP_part2 file names."""
    src = tmp_path / "recording.wav"
    src.touch()  # must not exist as the output target

    # Use a fresh directory so collision avoidance doesn't kick in
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    p1 = make_output_path(src, ".txt", out_dir, part=1)
    p2 = make_output_path(src, ".txt", out_dir, part=2)

    assert p1.name == "recording_WSP_part1.txt", f"Got {p1.name!r}"
    assert p2.name == "recording_WSP_part2.txt", f"Got {p2.name!r}"


@pytest.mark.integration
def test_max_stream_seconds_constant():
    """_MAX_STREAM_SECONDS must equal exactly 5 hours (18 000 seconds)."""
    assert _MAX_STREAM_SECONDS == 5 * 3600, (
        f"Expected 18000, got {_MAX_STREAM_SECONDS}"
    )

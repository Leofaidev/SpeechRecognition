"""Unit tests for library.retrainer — CHK-61."""

import numpy as np
import pytest
from pathlib import Path

from library.retrainer import LibraryRetrainer
from library.profile_creator import ProfileCreator
from library.storage import LibraryStorage


_SR = 16_000


def _fake_embed(audio: np.ndarray, sr: int) -> np.ndarray:
    return np.ones(192, dtype=np.float32)


def _make_audio(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * _SR), dtype=np.float32)


def _create_profile(storage, last, first, audio):
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="v1")
    return creator.create(audio, _SR, last=last, first=first)


# ---------------------------------------------------------------------------
# CHK-61: Missing sample file reported as failed
# ---------------------------------------------------------------------------

def test_retrainer_fails_on_missing_sample(tmp_path):
    storage = LibraryStorage(tmp_path)
    f1, _ = _create_profile(storage, "Alice", "A", _make_audio(10))

    # Remove the sample file
    (tmp_path / f1 / "sample_001.mp3").unlink()

    retrainer = LibraryRetrainer(storage, _fake_embed, new_checksum="v2")
    result = retrainer.retrain_all()

    assert result.failed == 1
    assert f1 in result.failed_profiles


def test_retrainer_succeeds_without_missing_samples(tmp_path):
    storage = LibraryStorage(tmp_path)
    _create_profile(storage, "Alice", "A", _make_audio(10))

    retrainer = LibraryRetrainer(storage, _fake_embed, new_checksum="v2")
    result = retrainer.retrain_all()

    assert result.retrained == 1
    assert result.failed == 0


def test_retrainer_updates_checksum(tmp_path):
    storage = LibraryStorage(tmp_path)
    f1, _ = _create_profile(storage, "Alice", "A", _make_audio(10))

    retrainer = LibraryRetrainer(storage, _fake_embed, new_checksum="v2")
    retrainer.retrain_all()

    meta = storage.read_meta(f1)
    assert meta.model_checksum == "v2"


def test_retrainer_progress_callback(tmp_path):
    storage = LibraryStorage(tmp_path)
    _create_profile(storage, "Alice", "A", _make_audio(10))
    _create_profile(storage, "Bob", "B", _make_audio(10))

    calls: list[tuple] = []

    def cb(folder, current, total):
        calls.append((folder, current, total))

    retrainer = LibraryRetrainer(storage, _fake_embed, progress_callback=cb)
    retrainer.retrain_all()

    assert len(calls) == 2
    # Each call has (folder_name, current_index, total)
    totals = {c[2] for c in calls}
    assert totals == {2}


def test_retrainer_partial_failure(tmp_path):
    storage = LibraryStorage(tmp_path)
    f1, _ = _create_profile(storage, "Alice", "A", _make_audio(10))
    f2, _ = _create_profile(storage, "Bob", "B", _make_audio(10))

    # Remove Alice's sample
    (tmp_path / f1 / "sample_001.mp3").unlink()

    retrainer = LibraryRetrainer(storage, _fake_embed, new_checksum="v2")
    result = retrainer.retrain_all()

    assert result.retrained == 1
    assert result.failed == 1


def test_retrainer_no_samples_entry_fails(tmp_path):
    storage = LibraryStorage(tmp_path)
    f1, meta = storage.create_profile("Lex", "L", "", "")
    # Leave samples=[] in JSON

    retrainer = LibraryRetrainer(storage, _fake_embed, new_checksum="v2")
    result = retrainer.retrain_all()

    assert result.failed == 1

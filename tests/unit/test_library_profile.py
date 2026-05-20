"""Unit tests for library.profile_creator — CHK-55, 56, 57, 58, 59."""

import numpy as np
import pytest
from pathlib import Path

from library.profile_creator import ProfileCreator, ConflictMode
from library.storage import LibraryStorage


# ---------------------------------------------------------------------------
# Mock embedding function — no model download needed
# ---------------------------------------------------------------------------

def _fake_embed(audio: np.ndarray, sr: int) -> np.ndarray:
    return np.ones(192, dtype=np.float32)


_SR = 16_000


def _make_audio(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * _SR), dtype=np.float32)


# ---------------------------------------------------------------------------
# CHK-55: Profile from 10s WAV — subfolder, sample_001, embedding, JSON
# ---------------------------------------------------------------------------

def test_create_profile_folder_exists(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="sha256:abc")
    creator.create(_make_audio(10), _SR, last="Smith", first="John")
    assert (tmp_path / "Smith_John__").exists()


def test_create_profile_sample_exists(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="sha256:abc")
    creator.create(_make_audio(10), _SR, last="Smith", first="John")
    assert (tmp_path / "Smith_John__" / "sample_001.mp3").exists()


def test_create_profile_embedding_exists(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="sha256:abc")
    creator.create(_make_audio(10), _SR, last="Smith", first="John")
    assert (tmp_path / "Smith_John__" / "embedding.npy").exists()


def test_create_profile_json_valid(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="sha256:abc")
    _, meta = creator.create(_make_audio(10), _SR, last="Smith", first="John")
    assert meta.last_name == "Smith"
    assert meta.sample_count == 1
    assert meta.samples == ["sample_001.mp3"]
    assert meta.model_checksum == "sha256:abc"


def test_create_profile_json_persisted(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="sha256:abc")
    creator.create(_make_audio(10), _SR, last="Smith", first="John")
    meta = storage.read_meta("Smith_John__")
    assert meta.last_name == "Smith"
    assert meta.samples == ["sample_001.mp3"]


# ---------------------------------------------------------------------------
# CHK-56: Profile from 1s WAV → low_confidence=True; files still created
# ---------------------------------------------------------------------------

def test_short_audio_sets_low_confidence(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed)
    _, meta = creator.create(_make_audio(1.0), _SR, last="Jane", first="Doe")
    assert meta.low_confidence is True


def test_short_audio_still_creates_files(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed)
    creator.create(_make_audio(1.0), _SR, last="Jane", first="Doe")
    folder = tmp_path / "Jane_Doe__"
    assert folder.exists()
    assert (folder / "sample_001.mp3").exists()
    assert (folder / "embedding.npy").exists()


def test_10s_audio_no_low_confidence(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed)
    _, meta = creator.create(_make_audio(10.0), _SR, last="Jane", first="Doe")
    assert meta.low_confidence is False


# ---------------------------------------------------------------------------
# CHK-57: Conflict overwrite — sample_001.mp3 replaced, sample list reset
# ---------------------------------------------------------------------------

def test_overwrite_replaces_sample(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="v1")
    creator.create(_make_audio(10), _SR, last="Alice", first="A")

    # Write a marker to sample_001 to confirm it gets replaced
    original = (tmp_path / "Alice_A__" / "sample_001.mp3").read_bytes()

    creator2 = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="v2")
    creator2.create(
        _make_audio(10), _SR, last="Alice", first="A",
        conflict_mode=ConflictMode.OVERWRITE
    )

    meta = storage.read_meta("Alice_A__")
    assert meta.samples == ["sample_001.mp3"]
    assert meta.sample_count == 1


def test_overwrite_resets_sample_list(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed)
    creator.create(_make_audio(10), _SR, last="Alice", first="A")
    # Manually add a second sample to the meta
    meta = storage.read_meta("Alice_A__")
    meta.samples.append("sample_002.mp3")
    meta.sample_count = 2
    storage.write_meta("Alice_A__", meta)

    creator.create(
        _make_audio(10), _SR, last="Alice", first="A",
        conflict_mode=ConflictMode.OVERWRITE
    )
    meta_after = storage.read_meta("Alice_A__")
    assert meta_after.sample_count == 1
    assert len(meta_after.samples) == 1


# ---------------------------------------------------------------------------
# CHK-58: Conflict merge — new sample_002.mp3; original unchanged; both in JSON
# ---------------------------------------------------------------------------

def test_merge_adds_sample_002(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed)
    creator.create(_make_audio(10), _SR, last="Bob", first="B")
    creator.create(
        _make_audio(10), _SR, last="Bob", first="B",
        conflict_mode=ConflictMode.MERGE
    )
    meta = storage.read_meta("Bob_B__")
    assert "sample_001.mp3" in meta.samples
    assert "sample_002.mp3" in meta.samples
    assert meta.sample_count == 2


def test_merge_original_sample_unchanged(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed)
    creator.create(_make_audio(10), _SR, last="Bob", first="B")
    original_bytes = (tmp_path / "Bob_B__" / "sample_001.mp3").read_bytes()
    creator.create(
        _make_audio(10), _SR, last="Bob", first="B",
        conflict_mode=ConflictMode.MERGE
    )
    assert (tmp_path / "Bob_B__" / "sample_001.mp3").read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# CHK-59: Conflict reject — folder unchanged
# ---------------------------------------------------------------------------

def test_reject_leaves_folder_unchanged(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed)
    creator.create(_make_audio(10), _SR, last="Carl", first="C")

    files_before = set(p.name for p in (tmp_path / "Carl_C__").iterdir())

    creator.create(
        _make_audio(10), _SR, last="Carl", first="C",
        conflict_mode=ConflictMode.REJECT
    )

    files_after = set(p.name for p in (tmp_path / "Carl_C__").iterdir())
    assert files_before == files_after


def test_reject_returns_existing_meta(tmp_path):
    storage = LibraryStorage(tmp_path)
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="v1")
    creator.create(_make_audio(10), _SR, last="Carl", first="C")

    creator2 = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="v2")
    _, meta = creator2.create(
        _make_audio(10), _SR, last="Carl", first="C",
        conflict_mode=ConflictMode.REJECT
    )
    assert meta.model_checksum == "v1"

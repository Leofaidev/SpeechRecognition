"""Unit tests for dictionary.store/matcher/importer/exporter — CHK-29 to 36."""

import csv
import textwrap
from dataclasses import replace
from pathlib import Path

import pytest

from dictionary.store import DictionaryStore
from dictionary.matcher import apply
from dictionary.importer import import_csv, ImportResult
from dictionary.exporter import export_csv
from transcription.engine import TranscribedSegment


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_seg(text: str, bad_audio: bool = False) -> TranscribedSegment:
    return TranscribedSegment(
        speaker_id="Speaker 1",
        start=0.0, end=3.0,
        text=text, language="English", language_code="en",
        confidence=0.9, no_speech_prob=0.1,
        bad_audio=bad_audio,
    )


# ---------------------------------------------------------------------------
# CHK-29: case-insensitive whole-word match
# ---------------------------------------------------------------------------

def test_case_insensitive_match():
    store = DictionaryStore()
    store.add("hello", "hi")
    segs = apply(store, [make_seg("Hello world")])
    assert segs[0].text == "hi world"


def test_case_insensitive_lower():
    store = DictionaryStore()
    store.add("hello", "hi")
    segs = apply(store, [make_seg("hello world")])
    assert segs[0].text == "hi world"


def test_case_insensitive_upper():
    store = DictionaryStore()
    store.add("hello", "hi")
    segs = apply(store, [make_seg("HELLO world")])
    assert segs[0].text == "hi world"


# ---------------------------------------------------------------------------
# CHK-30: whole-word — "Helloing" does NOT match "hello"
# ---------------------------------------------------------------------------

def test_whole_word_no_partial_match():
    store = DictionaryStore()
    store.add("hello", "hi")
    segs = apply(store, [make_seg("Helloing world")])
    assert segs[0].text == "Helloing world"


def test_whole_word_mid_word_not_matched():
    store = DictionaryStore()
    store.add("hello", "hi")
    segs = apply(store, [make_seg("sayhello")])
    assert segs[0].text == "sayhello"


# ---------------------------------------------------------------------------
# CHK-31: wildcard * matches multiple characters
# ---------------------------------------------------------------------------

def test_wildcard_star_matches_hello():
    store = DictionaryStore()
    store.add("hel*", "[word]")
    segs = apply(store, [make_seg("hello world")])
    assert "[word]" in segs[0].text


def test_wildcard_star_matches_help():
    store = DictionaryStore()
    store.add("hel*", "[word]")
    segs = apply(store, [make_seg("help me")])
    assert "[word]" in segs[0].text


def test_wildcard_star_matches_helpdesk():
    store = DictionaryStore()
    store.add("hel*", "[word]")
    segs = apply(store, [make_seg("helpdesk is open")])
    assert "[word]" in segs[0].text


# ---------------------------------------------------------------------------
# CHK-32: wildcard ? matches single character
# ---------------------------------------------------------------------------

def test_wildcard_question_matches_hello():
    store = DictionaryStore()
    store.add("h?llo", "[matched]")
    segs = apply(store, [make_seg("hello world")])
    assert "[matched]" in segs[0].text


def test_wildcard_question_no_match_too_short():
    store = DictionaryStore()
    store.add("h?llo", "[matched]")
    segs = apply(store, [make_seg("hllo world")])
    # "hllo" has no character between h and llo
    assert "[matched]" not in segs[0].text


# ---------------------------------------------------------------------------
# CHK-33: CSV import — 6 new, 4 conflicts
# ---------------------------------------------------------------------------

def test_import_csv_6_new_4_conflicts(tmp_path):
    # Pre-populate store with 4 entries that will conflict
    store = DictionaryStore()
    for i in range(4):
        store.add(f"existing{i}", f"replacement{i}")

    csv_path = tmp_path / "dict.csv"
    rows = []
    # 4 conflicting entries
    for i in range(4):
        rows.append(f"existing{i},newreplacement{i}")
    # 6 new entries
    for i in range(6):
        rows.append(f"newterm{i},newrepl{i}")

    csv_path.write_text("\n".join(rows), encoding="utf-8")

    result = import_csv(csv_path, store)

    assert result.added == 6
    assert result.rejected == 4
    assert len(result.rejected_sources) == 4


def test_import_csv_rejected_sources_listed(tmp_path):
    store = DictionaryStore()
    store.add("conflict1", "x")
    store.add("conflict2", "x")

    csv_path = tmp_path / "dict.csv"
    csv_path.write_text("conflict1,a\nconflict2,b\nnew1,c\n", encoding="utf-8")

    result = import_csv(csv_path, store)
    assert "conflict1" in result.rejected_sources
    assert "conflict2" in result.rejected_sources


# ---------------------------------------------------------------------------
# CHK-34: export → re-import round-trip
# ---------------------------------------------------------------------------

def test_export_reimport_round_trip(tmp_path):
    store = DictionaryStore()
    store.add("hello", "hi")
    store.add("goodbye", "bye")
    store.add("hel*", "greet")

    csv_path = tmp_path / "export.csv"
    export_csv(store, csv_path)

    store2 = DictionaryStore()
    result = import_csv(csv_path, store2)

    assert result.added == 3
    assert result.rejected == 0
    assert len(store2) == 3


# ---------------------------------------------------------------------------
# CHK-35: dictionary application does NOT alter confidence scores
# ---------------------------------------------------------------------------

def test_dictionary_does_not_change_confidence():
    store = DictionaryStore()
    store.add("hello", "hi")
    original = make_seg("hello world")
    original_confidence = original.confidence
    result = apply(store, [original])
    assert result[0].confidence == original_confidence


def test_dictionary_does_not_change_no_speech_prob():
    store = DictionaryStore()
    store.add("hello", "hi")
    original = make_seg("hello world")
    result = apply(store, [original])
    assert result[0].no_speech_prob == original.no_speech_prob


# ---------------------------------------------------------------------------
# CHK-36: dictionary NOT applied to bad_audio segments
# ---------------------------------------------------------------------------

def test_dictionary_skips_bad_audio_segments():
    store = DictionaryStore()
    store.add("XXXXX", "replaced")
    bad_seg = make_seg("XXXXX", bad_audio=True)
    result = apply(store, [bad_seg])
    assert result[0].text == "XXXXX"


# ---------------------------------------------------------------------------
# Store basics
# ---------------------------------------------------------------------------

def test_store_add_and_get():
    store = DictionaryStore()
    store.add("test", "result")
    entry = store.get("test")
    assert entry is not None
    assert entry.replacement == "result"


def test_store_conflict_returns_false():
    store = DictionaryStore()
    store.add("test", "result")
    ok = store.add("test", "other")
    assert ok is False


def test_store_remove():
    store = DictionaryStore()
    store.add("test", "result")
    store.remove("test")
    assert store.get("test") is None


def test_store_len():
    store = DictionaryStore()
    store.add("a", "1")
    store.add("b", "2")
    assert len(store) == 2


def test_store_persistence(tmp_path):
    path = tmp_path / "dict.json"
    store = DictionaryStore(path)
    store.add("hello", "hi")

    store2 = DictionaryStore(path)
    assert store2.get("hello") is not None
    assert store2.get("hello").replacement == "hi"

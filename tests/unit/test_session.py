"""Unit tests for session.manager and session.history — CHK-68 to 73."""

import json
import pytest
from pathlib import Path

from session.manager import SessionManager, SessionSegment
from session import history as session_history
from transcription.engine import TranscribedSegment


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_transcribed(text: str, speaker: str = "Speaker 1",
                     start: float = 0.0, end: float = 3.0) -> TranscribedSegment:
    return TranscribedSegment(
        speaker_id=speaker,
        start=start, end=end,
        text=text, language="English", language_code="en",
        confidence=0.9, no_speech_prob=0.1,
    )


def make_manager_with_segments(n: int = 5, speaker: str = "Speaker 1") -> SessionManager:
    mgr = SessionManager(source_type="file", source_path="interview.mp3")
    segs = [make_transcribed(f"text {i}", speaker=speaker, start=float(i), end=float(i+2))
            for i in range(n)]
    mgr.add_segments(segs)
    return mgr


# ---------------------------------------------------------------------------
# CHK-68: Retroactive relabelling — 5 segments all renamed
# ---------------------------------------------------------------------------

def test_relabel_updates_all_matching_segments():
    mgr = make_manager_with_segments(5, "Speaker 1")
    count = mgr.relabel("Speaker 1", "Alice")
    assert count == 5
    for seg in mgr.segments:
        assert seg.speaker_name == "Alice"


def test_relabel_returns_update_count():
    mgr = make_manager_with_segments(3, "Speaker 1")
    count = mgr.relabel("Speaker 1", "Bob")
    assert count == 3


def test_relabel_only_affects_matching_speaker():
    mgr = SessionManager()
    mgr.add_segments([
        make_transcribed("hello", speaker="Speaker 1"),
        make_transcribed("world", speaker="Speaker 2"),
    ])
    mgr.relabel("Speaker 1", "Alice")
    names = [s.speaker_name for s in mgr.segments]
    assert names == ["Alice", "Speaker 2"]


def test_relabel_no_match_returns_zero():
    mgr = make_manager_with_segments(3, "Speaker 1")
    count = mgr.relabel("Speaker 99", "Nobody")
    assert count == 0


# ---------------------------------------------------------------------------
# CHK-69: Skipped speaker retains original label
# ---------------------------------------------------------------------------

def test_skipped_speaker_retains_label():
    mgr = SessionManager()
    mgr.add_segments([make_transcribed("text", speaker="Speaker 1")])
    mgr.skip_speaker("Speaker 1")
    assert mgr.segments[0].speaker_name == "Speaker 1"


def test_unannotated_speaker_retains_speaker_n_label():
    mgr = make_manager_with_segments(2, "Speaker 1")
    # Save without any relabelling
    d = mgr.to_dict()
    for seg in d["segments"]:
        assert seg["speaker_name"] == "Speaker 1"


# ---------------------------------------------------------------------------
# CHK-70: Session saved to sessions/ folder; reloaded produces identical list
# ---------------------------------------------------------------------------

def test_session_save_and_reload(tmp_path):
    mgr = make_manager_with_segments(3)
    session_history.save(tmp_path, mgr)

    loaded = session_history.load(tmp_path, mgr.session_id)
    assert loaded.session_id == mgr.session_id
    assert len(loaded.segments) == 3


def test_session_segments_survive_round_trip(tmp_path):
    mgr = SessionManager()
    mgr.add_segments([make_transcribed("Hello world", speaker="Alice")])
    session_history.save(tmp_path, mgr)

    loaded = session_history.load(tmp_path, mgr.session_id)
    assert loaded.segments[0].speaker_name == "Alice"
    assert loaded.segments[0].text == "Hello world"


def test_session_file_is_valid_json(tmp_path):
    mgr = make_manager_with_segments(2)
    path = session_history.save(tmp_path, mgr)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "session_id" in data
    assert "segments" in data


def test_session_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        session_history.load(tmp_path, "nonexistent-id")


def test_session_delete(tmp_path):
    mgr = make_manager_with_segments(1)
    session_history.save(tmp_path, mgr)
    session_history.delete(tmp_path, mgr.session_id)
    with pytest.raises(FileNotFoundError):
        session_history.load(tmp_path, mgr.session_id)


def test_list_sessions(tmp_path):
    m1 = make_manager_with_segments(1)
    m2 = make_manager_with_segments(2)
    session_history.save(tmp_path, m1)
    session_history.save(tmp_path, m2)
    sessions = session_history.list_sessions(tmp_path)
    assert len(sessions) == 2
    ids = {s["session_id"] for s in sessions}
    assert m1.session_id in ids
    assert m2.session_id in ids


# ---------------------------------------------------------------------------
# CHK-71: Output regeneration produces file with current config
# ---------------------------------------------------------------------------

def test_regenerate_output_creates_file(tmp_path):
    session_dir = tmp_path / "sessions"
    output_dir = tmp_path / "output"
    mgr = make_manager_with_segments(2)
    session_history.save(session_dir, mgr)

    written = session_history.regenerate_output(
        session_dir, mgr.session_id, output_dir, formats=["txt"]
    )
    assert len(written) == 1
    assert written[0].exists()


def test_regenerate_output_reflects_field_config(tmp_path):
    session_dir = tmp_path / "sessions"
    output_dir = tmp_path / "output"
    mgr = make_manager_with_segments(1)
    session_history.save(session_dir, mgr)

    # Regenerate with language disabled
    fields = {"timestamp": True, "speaker": True, "language": False,
               "confidence": True, "text": True}
    written = session_history.regenerate_output(
        session_dir, mgr.session_id, output_dir,
        fields=fields, formats=["txt"]
    )
    content = written[0].read_text(encoding="utf-8")
    assert "Language:" not in content


# ---------------------------------------------------------------------------
# CHK-72: Regenerated file gets collision-safe name
# ---------------------------------------------------------------------------

def test_regenerate_output_collision_avoidance(tmp_path):
    session_dir = tmp_path / "sessions"
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)

    mgr = SessionManager(source_path="interview.mp3")
    mgr.add_segments([make_transcribed("hello")])
    session_history.save(session_dir, mgr)

    # Pre-create the first output to force collision
    (output_dir / "interview_WSP.txt").write_text("existing")

    written = session_history.regenerate_output(
        session_dir, mgr.session_id, output_dir, formats=["txt"]
    )
    assert written[0].name == "interview_WSP_2.txt"


# ---------------------------------------------------------------------------
# CHK-73: Editing speaker profile sets output_outdated = true
# ---------------------------------------------------------------------------

def test_mark_outdated_sets_flag(tmp_path):
    mgr = SessionManager()
    mgr.add_segments([make_transcribed("hello", speaker="Alice")])
    session_history.save(tmp_path, mgr)

    count = session_history.mark_outdated(tmp_path, "Alice")
    assert count == 1

    loaded = session_history.load(tmp_path, mgr.session_id)
    assert loaded.output_outdated is True


def test_mark_outdated_sets_segment_flag(tmp_path):
    mgr = SessionManager()
    mgr.add_segments([make_transcribed("hello", speaker="Alice")])
    session_history.save(tmp_path, mgr)

    session_history.mark_outdated(tmp_path, "Alice")

    path = tmp_path / f"{mgr.session_id}.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    assert d["segments"][0]["output_outdated"] is True


def test_mark_outdated_no_match_returns_zero(tmp_path):
    mgr = make_manager_with_segments(1, "Bob")
    session_history.save(tmp_path, mgr)

    count = session_history.mark_outdated(tmp_path, "Alice")
    assert count == 0


def test_mark_outdated_only_affects_matching_speaker(tmp_path):
    mgr = SessionManager()
    mgr.add_segments([
        make_transcribed("hi", speaker="Alice"),
        make_transcribed("hello", speaker="Bob"),
    ])
    session_history.save(tmp_path, mgr)

    session_history.mark_outdated(tmp_path, "Alice")

    path = tmp_path / f"{mgr.session_id}.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    alice_seg = next(s for s in d["segments"] if s["speaker_name"] == "Alice")
    bob_seg = next(s for s in d["segments"] if s["speaker_name"] == "Bob")
    assert alice_seg["output_outdated"] is True
    assert bob_seg["output_outdated"] is False


# ---------------------------------------------------------------------------
# SessionManager basics
# ---------------------------------------------------------------------------

def test_session_manager_has_uuid():
    mgr = SessionManager()
    assert len(mgr.session_id) == 36  # UUID format


def test_add_segments_index_sequential():
    mgr = SessionManager()
    mgr.add_segments([make_transcribed("a"), make_transcribed("b")])
    indices = [s.index for s in mgr.segments]
    assert indices == [0, 1]


def test_to_dict_roundtrip():
    mgr = make_manager_with_segments(2)
    d = mgr.to_dict()
    restored = SessionManager.from_dict(d)
    assert restored.session_id == mgr.session_id
    assert len(restored.segments) == 2

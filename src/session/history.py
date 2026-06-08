"""Session history persistence and output regeneration (T-53, T-54, T-55, T-56)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from session.manager import SessionManager, SessionSegment

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def save(session_dir: Path | str, manager: SessionManager) -> Path:
    """Save *manager* as a JSON file in *session_dir*.

    Returns the path of the saved file.
    """
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / f"{manager.session_id}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(manager.to_dict(), fh, indent=2, ensure_ascii=False)
    return path


def load(session_dir: Path | str, session_id: str) -> SessionManager:
    """Load a session by ID.  Raises FileNotFoundError if not found."""
    path = Path(session_dir) / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    with path.open(encoding="utf-8") as fh:
        return SessionManager.from_dict(json.load(fh))


def list_sessions(session_dir: Path | str) -> list[dict]:
    """Return a sorted list of session summary dicts (newest first).

    Each dict has: session_id, created_at, source_type, source_path,
    output_outdated, segment_count.
    """
    session_dir = Path(session_dir)
    if not session_dir.exists():
        return []

    summaries: list[dict] = []
    for path in session_dir.glob("*.json"):
        try:
            with path.open(encoding="utf-8") as fh:
                d = json.load(fh)
            segments = d.get("segments", [])
            duration = _parse_srt_time(segments[-1].get("end_time", "")) if segments else 0.0
            seen: dict[str, bool] = {}
            for seg in segments:
                name = seg.get("speaker_name", "")
                if name:
                    seen[name] = True
            summaries.append({
                "session_id":      d.get("session_id", path.stem),
                "created_at":      d.get("created_at", ""),
                "source_type":     d.get("source_type", ""),
                "source_path":     d.get("source_path"),
                "output_outdated": d.get("output_outdated", False),
                "segment_count":   len(segments),
                "duration_seconds": duration,
                "speakers":        list(seen.keys()),
            })
        except (json.JSONDecodeError, OSError):
            pass

    summaries.sort(key=lambda s: s["created_at"], reverse=True)
    return summaries


def delete(session_dir: Path | str, session_id: str) -> None:
    """Delete a session JSON file.  No-op if not found."""
    path = Path(session_dir) / f"{session_id}.json"
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# T-54: output regeneration
# ---------------------------------------------------------------------------

def regenerate_output(
    session_dir: Path | str,
    session_id: str,
    output_dir: Path | str,
    fields: dict[str, bool] | None = None,
    formats: list[str] | None = None,
) -> list[Path]:
    """Reload a session and write new output files with current field config.

    Parameters
    ----------
    session_dir:
        Directory containing session JSON files.
    session_id:
        Session to regenerate.
    output_dir:
        Where to write new output files.
    fields:
        Output field configuration.  Defaults to all fields enabled.
    formats:
        List of format strings: "txt", "srt", "json", "docx".

    Returns
    -------
    List of output file paths written.
    """
    from output import txt_writer, srt_writer, json_writer, docx_writer
    from output.naming import make_output_path
    from transcription.engine import TranscribedSegment

    manager = load(session_dir, session_id)
    output_dir = Path(output_dir)
    formats = formats or ["txt"]

    # Reconstruct TranscribedSegment objects from session segments
    ts_segments = [
        TranscribedSegment(
            speaker_id=s.speaker_name,
            start=_parse_srt_time(s.start_time),
            end=_parse_srt_time(s.end_time),
            text=s.text,
            language=s.language or "Unknown",
            language_code="",
            confidence=s.transcription_confidence,
            no_speech_prob=0.0,
            bad_audio=s.bad_audio,
        )
        for s in manager.segments
    ]

    source_stem = Path(manager.source_path).stem if manager.source_path else "session"
    written: list[Path] = []

    for fmt in formats:
        ext = f".{fmt}"
        out_path = make_output_path(
            Path(source_stem + ".tmp"),
            ext,
            output_dir,
        )
        if fmt == "txt":
            txt_writer.write(ts_segments, out_path, fields=fields)
        elif fmt == "srt":
            srt_writer.write(ts_segments, out_path)
        elif fmt == "json":
            json_writer.write(ts_segments, out_path)
        elif fmt == "docx":
            docx_writer.write(ts_segments, out_path, fields=fields)
        written.append(out_path)

    return written


# ---------------------------------------------------------------------------
# T-55: outdated-output detection
# ---------------------------------------------------------------------------

def mark_outdated(session_dir: Path | str, speaker_name: str) -> int:
    """Set output_outdated=true on all sessions that reference *speaker_name*.

    Called when a speaker profile is edited (name change or re-embedding).

    Returns the number of sessions updated.
    """
    session_dir = Path(session_dir)
    if not session_dir.exists():
        return 0

    updated = 0
    for path in session_dir.glob("*.json"):
        try:
            with path.open(encoding="utf-8") as fh:
                d = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue

        changed = False
        for seg in d.get("segments", []):
            if seg.get("speaker_name") == speaker_name:
                seg["output_outdated"] = True
                changed = True

        if changed:
            d["output_outdated"] = True
            with path.open("w", encoding="utf-8") as fh:
                json.dump(d, fh, indent=2, ensure_ascii=False)
            updated += 1

    return updated


# ---------------------------------------------------------------------------
# T-56: CLI-facing helpers (called by cli.parser in Phase 5)
# ---------------------------------------------------------------------------

def print_session_list(session_dir: Path | str) -> None:
    """Print a tabular summary of all sessions to stdout."""
    sessions = list_sessions(session_dir)
    if not sessions:
        print("No sessions found.")
        return
    header = f"{'Session ID':<38}  {'Created':>24}  {'Type':<12}  {'Segments':>8}  Outdated"
    print(header)
    print("-" * len(header))
    for s in sessions:
        outdated = "Yes" if s["output_outdated"] else "No"
        print(
            f"{s['session_id']:<38}  {s['created_at']:>24}  "
            f"{s['source_type']:<12}  {s['segment_count']:>8}  {outdated}"
        )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _parse_srt_time(t: str) -> float:
    """Parse HH:MM:SS,mmm → seconds."""
    try:
        hms, ms = t.split(",")
        h, m, s = hms.split(":")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    except (ValueError, AttributeError):
        return 0.0

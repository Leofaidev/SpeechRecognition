"""Session lifecycle management (T-51, T-52).

SessionManager holds all data for one processing run and supports
post-session retroactive speaker relabelling.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


def _srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


@dataclass
class SessionSegment:
    index: int
    speaker_name: str
    start_time: str          # HH:MM:SS,mmm
    end_time: str
    language: str | None
    text: str
    translated_text: str | None
    transcription_confidence: float
    speaker_confidence: float
    bad_audio: bool
    output_outdated: bool = False

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "speaker_name": self.speaker_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "language": self.language,
            "text": self.text,
            "translated_text": self.translated_text,
            "transcription_confidence": round(self.transcription_confidence, 5),
            "speaker_confidence": round(self.speaker_confidence, 4),
            "bad_audio": self.bad_audio,
            "output_outdated": self.output_outdated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SessionSegment":
        return cls(
            index=d["index"],
            speaker_name=d["speaker_name"],
            start_time=d["start_time"],
            end_time=d["end_time"],
            language=d.get("language"),
            text=d["text"],
            translated_text=d.get("translated_text"),
            transcription_confidence=d.get("transcription_confidence", 0.0),
            speaker_confidence=d.get("speaker_confidence", 0.0),
            bad_audio=d.get("bad_audio", False),
            output_outdated=d.get("output_outdated", False),
        )


class SessionManager:
    """Manages a single processing session.

    Parameters
    ----------
    source_type:
        "file", "batch", "microphone", or "webcam".
    source_path:
        Absolute path to source file, or None for mic/webcam.
    speaker_group:
        Name of the active voice library group.
    session_id:
        UUID string; auto-generated if not provided.
    """

    def __init__(
        self,
        source_type: str = "file",
        source_path: str | None = None,
        speaker_group: str = "",
        session_id: str | None = None,
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.source_type = source_type
        self.source_path = source_path
        self.speaker_group = speaker_group
        self.output_files: list[str] = []
        self.last_clipboard_text: str | None = None
        self.output_outdated: bool = False
        self._segments: list[SessionSegment] = []

    # ------------------------------------------------------------------
    # segment management
    # ------------------------------------------------------------------

    def add_segments(
        self,
        transcribed: list["TranscribedSegment"],
        speaker_confidence: float = 0.0,
    ) -> None:
        """Convert TranscribedSegment objects and append to session."""
        offset = len(self._segments)
        for i, seg in enumerate(transcribed):
            self._segments.append(
                SessionSegment(
                    index=offset + i,
                    speaker_name=seg.speaker_id,
                    start_time=_srt_time(seg.start),
                    end_time=_srt_time(seg.end),
                    language=seg.language,
                    text=seg.text,
                    translated_text=None,
                    transcription_confidence=seg.confidence,
                    speaker_confidence=speaker_confidence,
                    bad_audio=seg.bad_audio,
                )
            )

    @property
    def segments(self) -> list[SessionSegment]:
        return list(self._segments)

    # ------------------------------------------------------------------
    # T-52: retroactive relabelling
    # ------------------------------------------------------------------

    def relabel(self, old_speaker_id: str, new_speaker_name: str) -> int:
        """Replace *old_speaker_id* with *new_speaker_name* in all segments.

        Returns the number of segments updated.
        """
        count = 0
        for seg in self._segments:
            if seg.speaker_name == old_speaker_id:
                seg.speaker_name = new_speaker_name
                count += 1
        return count

    def skip_speaker(self, speaker_id: str) -> None:
        """Mark a speaker as intentionally not relabelled.

        The speaker retains its current label (e.g. "Speaker 1").
        This is a no-op in terms of data; it documents the user's intent.
        """
        pass  # label already in place; no modification needed

    # ------------------------------------------------------------------
    # serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "speaker_group": self.speaker_group,
            "output_files": self.output_files,
            "last_clipboard_text": self.last_clipboard_text,
            "output_outdated": self.output_outdated,
            "segments": [s.to_dict() for s in self._segments],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SessionManager":
        mgr = cls(
            source_type=d.get("source_type", "file"),
            source_path=d.get("source_path"),
            speaker_group=d.get("speaker_group", ""),
            session_id=d.get("session_id"),
        )
        mgr.created_at = d.get("created_at", mgr.created_at)
        mgr.output_files = d.get("output_files", [])
        mgr.last_clipboard_text = d.get("last_clipboard_text")
        mgr.output_outdated = d.get("output_outdated", False)
        mgr._segments = [SessionSegment.from_dict(s) for s in d.get("segments", [])]
        return mgr

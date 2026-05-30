"""Write transcribed segments to a plain-text file.

Format (Spec 8.4.c): each enabled field on its own line, segments separated
by blank lines.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


def _format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def write(
    segments: list["TranscribedSegment"],
    path: Path | str,
    fields: dict[str, bool] | None = None,
) -> Path:
    """Write *segments* to *path* as plain text.

    Parameters
    ----------
    segments:
        List of TranscribedSegment objects.
    path:
        Output file path.
    fields:
        Dict of ``{field_name: bool}`` controlling which fields appear.
        Defaults to all fields enabled.

    Returns
    -------
    The path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _fields = fields or {
        "timestamp": True,
        "speaker": True,
        "language": True,
        "confidence": True,
        "text": True,
        "translation": False,
    }

    blocks: list[str] = []
    for seg in segments:
        lines: list[str] = []
        if _fields.get("timestamp", True):
            lines.append(f"{_format_time(seg.start)} --> {_format_time(seg.end)}")
        if _fields.get("speaker", True):
            lines.append(f"Speaker: {seg.speaker_id}")
        if _fields.get("language", True):
            lines.append(f"Language: {seg.language}")
        if _fields.get("confidence", True):
            lines.append(f"Confidence: {seg.confidence:.2f}")
        if _fields.get("text", True):
            lines.append(f"Text: {seg.text}")
        if _fields.get("translation", False) and seg.translated_text:
            lines.append(f"Translation: {seg.translated_text}")
        blocks.append("\n".join(lines))

    with path.open("w", encoding="utf-8") as fh:
        fh.write("\n\n".join(blocks))
        if blocks:
            fh.write("\n")

    return path

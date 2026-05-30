"""Write transcribed segments to an SRT subtitle file.

Format (Spec 8.4.d):
- Standard SRT numbering (1-based sequential index).
- Timestamp: HH:MM:SS,mmm --> HH:MM:SS,mmm
- Speaker name on the text line if available (no language prefix).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


def _srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write(
    segments: list["TranscribedSegment"],
    path: Path | str,
    fields: dict[str, bool] | None = None,
) -> Path:
    """Write *segments* to *path* in SRT format.

    The language prefix is always suppressed (Spec 8.4.d).
    Speaker name is prepended to the subtitle text if available.
    When *fields* has ``translation`` set to True, translated text is used.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    use_translation = bool((fields or {}).get("translation", False))

    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        text = (seg.translated_text or seg.text) if use_translation else seg.text
        lines.append(str(i))
        lines.append(f"{_srt_time(seg.start)} --> {_srt_time(seg.end)}")
        if seg.speaker_id and seg.speaker_id != "Unknown":
            lines.append(f"{seg.speaker_id}: {text}")
        else:
            lines.append(text)
        lines.append("")  # blank line separator

    with path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return path

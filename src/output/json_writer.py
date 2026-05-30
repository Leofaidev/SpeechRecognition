"""Write transcribed segments to a JSON file.

Per Spec 8.4.e: all 6 fields are always present in the JSON output regardless
of the field_selector configuration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


def write(segments: list["TranscribedSegment"], path: Path | str) -> Path:
    """Write all segments to *path* as a JSON array.

    All 6 fields (timestamp, speaker, language, confidence, text,
    no_speech_prob) are included for every segment, regardless of the
    field selector configuration.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = [
        {
            "start": seg.start,
            "end": seg.end,
            "speaker": seg.speaker_id,
            "language": seg.language,
            "language_code": seg.language_code,
            "confidence": seg.confidence,
            "no_speech_prob": seg.no_speech_prob,
            "bad_audio": seg.bad_audio,
            "low_confidence": seg.low_confidence,
            "text": seg.text,
            "translated_text": seg.translated_text,
        }
        for seg in segments
    ]

    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    return path

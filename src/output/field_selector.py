"""Apply output content configuration to segments before writing.

Each field can be individually enabled/disabled in config.output_fields.
The JSON writer always receives all 6 fields regardless of this selector.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


_ALL_FIELDS = ("timestamp", "speaker", "language", "confidence", "text", "original_text")


class FieldSelector:
    """Filter segment fields according to active output configuration.

    Parameters
    ----------
    config:
        ConfigStore instance.  Key: ``output_fields`` (dict of bool flags).
    """

    def __init__(self, config) -> None:
        self._config = config

    def is_enabled(self, field: str) -> bool:
        fields = self._config.get("output_fields", {})
        return bool(fields.get(field, True))

    def apply(self, segments: list["TranscribedSegment"]) -> list[dict]:
        """Return a list of dicts with only the enabled fields."""
        result: list[dict] = []
        for seg in segments:
            row: dict = {}
            if self.is_enabled("timestamp"):
                row["timestamp_start"] = seg.start
                row["timestamp_end"] = seg.end
            if self.is_enabled("speaker"):
                row["speaker"] = seg.speaker_id
            if self.is_enabled("language"):
                row["language"] = seg.language
            if self.is_enabled("confidence"):
                row["confidence"] = seg.confidence
            if self.is_enabled("text"):
                row["text"] = seg.text
            result.append(row)
        return result

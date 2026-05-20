"""Apply substitution dictionary to transcribed segments.

Rules (Spec 7.2)
----------------
- Case-insensitive whole-word matching.
- fnmatch wildcards (* and ?) supported in source terms.
- Dictionary is NOT applied to speaker confidence scores.
- Dictionary is NOT applied on the retraining code path (caller's responsibility).
"""

from __future__ import annotations

import fnmatch
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dictionary.store import DictionaryStore
    from transcription.engine import TranscribedSegment


def _word_boundary_sub(pattern: str, replacement: str, text: str) -> str:
    """Whole-word, case-insensitive replacement for a literal pattern."""
    escaped = re.escape(pattern)
    regex = re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)
    return regex.sub(replacement, text)


def _wildcard_sub(pattern: str, replacement: str, text: str) -> str:
    """Word-level fnmatch wildcard substitution (case-insensitive)."""
    words = text.split(" ")
    result: list[str] = []
    for word in words:
        # Strip leading/trailing punctuation for matching, preserve it
        stripped = word.strip(".,!?;:\"'()")
        if fnmatch.fnmatchcase(stripped.lower(), pattern.lower()):
            # Replace the matched part, keep surrounding punctuation
            prefix = word[: len(word) - len(word.lstrip(".,!?;:\"'()"))]
            suffix = word[len(word.rstrip(".,!?;:\"'()")) :]
            result.append(prefix + replacement + suffix)
        else:
            result.append(word)
    return " ".join(result)


def _is_wildcard(pattern: str) -> bool:
    return "*" in pattern or "?" in pattern


def apply(store: "DictionaryStore", segments: list["TranscribedSegment"]) -> list["TranscribedSegment"]:
    """Return a new list of segments with substitutions applied.

    Confidence scores are not modified.  ``bad_audio`` segments are skipped.
    """
    if len(store) == 0:
        return segments

    result: list["TranscribedSegment"] = []
    for seg in segments:
        if seg.bad_audio:
            result.append(seg)
            continue

        text = seg.text
        original_text = text  # preserve pre-substitution for output

        for entry in store:
            if _is_wildcard(entry.source):
                text = _wildcard_sub(entry.source, entry.replacement, text)
            else:
                text = _word_boundary_sub(entry.source, entry.replacement, text)

        # Return a new segment with updated text; confidence unchanged
        from dataclasses import replace
        result.append(replace(seg, text=text))

    return result

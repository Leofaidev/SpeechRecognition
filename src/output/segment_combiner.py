"""Merge consecutive same-speaker segments before writing TXT / DOCX output."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


def combine_consecutive(
    segments: list["TranscribedSegment"],
) -> list["TranscribedSegment"]:
    """Return a new list merging consecutive segments that share speaker and language.

    Bad-audio segments are never merged — they act as a hard break.
    The input list is not mutated.
    """
    if not segments:
        return []

    result: list["TranscribedSegment"] = []
    group: list["TranscribedSegment"] = [segments[0]]

    for seg in segments[1:]:
        prev = group[-1]
        can_merge = (
            not seg.bad_audio
            and not prev.bad_audio
            and seg.speaker_id == prev.speaker_id
            and seg.language == prev.language
        )
        if can_merge:
            group.append(seg)
        else:
            result.append(_merge(group))
            group = [seg]

    result.append(_merge(group))
    return result


def _merge(group: list["TranscribedSegment"]) -> "TranscribedSegment":
    if len(group) == 1:
        return group[0]

    from transcription.engine import TranscribedSegment

    first = group[0]
    last = group[-1]
    texts = [s.text for s in group if s.text]
    translations = [s.translated_text for s in group if s.translated_text]
    avg_conf = sum(s.confidence for s in group) / len(group)
    avg_no_speech = sum(s.no_speech_prob for s in group) / len(group)

    return TranscribedSegment(
        speaker_id=first.speaker_id,
        start=first.start,
        end=last.end,
        text=" ".join(texts),
        language=first.language,
        language_code=first.language_code,
        confidence=avg_conf,
        no_speech_prob=avg_no_speech,
        translated_text=" ".join(translations) if translations else None,
        bad_audio=False,
        low_confidence=any(s.low_confidence for s in group),
    )

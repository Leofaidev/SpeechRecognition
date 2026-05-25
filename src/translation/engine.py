"""Translation dispatcher.

Routes to the active engine (local OPUS-MT or Google Translate).
Translation is always applied AFTER the substitution dictionary.
When translation is disabled, input text is returned unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


class TranslationEngine:
    """Apply translation to a list of TranscribedSegment objects.

    Parameters
    ----------
    config:
        ConfigStore instance.  Keys used:
        - translation_enabled (bool)
        - translation_engine ("local" | "google")
        - source_language (str)
        - target_language (str)
    """

    def __init__(self, config) -> None:
        self._config = config
        self._opus_translators: dict = {}  # keyed by (source, target)

    def translate(self, segments: list["TranscribedSegment"]) -> list["TranscribedSegment"]:
        """Return segments with ``text`` translated if translation is enabled.

        If translation is disabled, segments are returned unchanged.
        Bad-audio segments are skipped.
        """
        if not self._config.get("translation_enabled", False):
            return segments

        engine = self._config.get("translation_engine", "local")
        source = self._config.get("source_language", "auto")
        target = self._config.get("target_language", "en")

        active = [seg for seg in segments if not seg.bad_audio]
        if not active:
            return segments

        if engine == "google":
            from translation.google import translate
            texts = [seg.text for seg in active]
            translated = translate(texts, source, target)
        elif source == "auto":
            translated = self._translate_local_auto(active, target)
        else:
            texts = [seg.text for seg in active]
            translated = self._translate_local(texts, source, target)

        from dataclasses import replace
        result: list["TranscribedSegment"] = []
        translated_iter = iter(translated)
        for seg in segments:
            if seg.bad_audio:
                result.append(seg)
            else:
                result.append(replace(seg, translated_text=next(translated_iter)))
        return result

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _translate_local(self, texts: list[str], source: str, target: str) -> list[str]:
        key = (source, target)
        if key not in self._opus_translators:
            from translation.opus_mt import OpusMTTranslator
            self._opus_translators[key] = OpusMTTranslator(source, target)
        return self._opus_translators[key].translate(texts)

    def _translate_local_auto(self, active_segments: list, target: str) -> list[str]:
        """Translate each segment using its detected language_code.

        Falls back to a two-step path through English when no direct model exists
        for the detected-source → target pair (e.g. ru→de has no OPUS-MT model,
        but ru→en→de works via two existing models).
        """
        results: list[str] = []
        for seg in active_segments:
            src = getattr(seg, "language_code", None) or ""
            if not src or src == target:
                results.append(seg.text)
                continue
            try:
                results.append(self._translate_local([seg.text], src, target)[0])
            except Exception:
                # Direct model unavailable; try two-step via English
                translated = seg.text
                if src != "en" and target != "en":
                    try:
                        en_text = self._translate_local([seg.text], src, "en")[0]
                        translated = self._translate_local([en_text], "en", target)[0]
                    except Exception:
                        pass
                results.append(translated)
        return results

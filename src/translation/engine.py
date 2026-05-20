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
        self._opus_translator = None

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

        texts_to_translate = [
            seg.text for seg in segments if not seg.bad_audio
        ]
        if not texts_to_translate:
            return segments

        if engine == "google":
            from translation.google import translate
            translated = translate(texts_to_translate, source, target)
        else:
            translated = self._translate_local(texts_to_translate, source, target)

        from dataclasses import replace
        result: list["TranscribedSegment"] = []
        translated_iter = iter(translated)
        for seg in segments:
            if seg.bad_audio:
                result.append(seg)
            else:
                result.append(replace(seg, text=next(translated_iter)))
        return result

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _translate_local(self, texts: list[str], source: str, target: str) -> list[str]:
        if self._opus_translator is None:
            from translation.opus_mt import OpusMTTranslator
            self._opus_translator = OpusMTTranslator(source, target)
        return self._opus_translator.translate(texts)

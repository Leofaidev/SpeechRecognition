"""Local translation via Helsinki-NLP OPUS-MT (transformers library).

Models are downloaded on first use and cached by the transformers library.
"""

from __future__ import annotations

from dataclasses import dataclass

_QUALITY_WARNING_PAIRS: set[tuple[str, str]] = {
    ("en", "zh"),
    ("en", "zh-cn"),
    ("en", "zh-tw"),
    ("zh", "en"),
    ("zh-cn", "en"),
    ("zh-tw", "en"),
}


@dataclass
class LanguagePairInfo:
    source: str
    target: str
    model_name: str
    quality_warning: bool = False


def get_language_pair_info(source: str, target: str) -> LanguagePairInfo:
    """Return metadata for a translation pair including quality warning."""
    model_name = f"Helsinki-NLP/opus-mt-{source}-{target}"
    quality_warning = (source.lower(), target.lower()) in _QUALITY_WARNING_PAIRS
    return LanguagePairInfo(
        source=source,
        target=target,
        model_name=model_name,
        quality_warning=quality_warning,
    )


class OpusMTTranslator:
    """Translate text using a local OPUS-MT model.

    Parameters
    ----------
    source_lang:
        ISO 639-1 source language code (e.g. "en").
    target_lang:
        ISO 639-1 target language code (e.g. "fi").
    progress_callback:
        Called with (bytes_downloaded, total_bytes) during model download.
    """

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        progress_callback=None,
    ) -> None:
        self._source = source_lang
        self._target = target_lang
        self._progress_cb = progress_callback
        self._tokenizer = None
        self._model = None

    @property
    def pair_info(self) -> LanguagePairInfo:
        return get_language_pair_info(self._source, self._target)

    def translate(self, texts: list[str]) -> list[str]:
        """Translate a list of strings.  Returns translated strings in order."""
        if not texts:
            return []
        tokenizer, model = self._get_model()
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        translated = model.generate(**inputs)
        return [tokenizer.decode(t, skip_special_tokens=True) for t in translated]

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _get_model(self):
        if self._tokenizer is None or self._model is None:
            self._tokenizer, self._model = self._load_model()
        return self._tokenizer, self._model

    def _load_model(self):
        from transformers import MarianMTModel, MarianTokenizer

        model_name = f"Helsinki-NLP/opus-mt-{self._source}-{self._target}"

        def _try_load():
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            return tokenizer, model

        try:
            return _try_load()
        except Exception as exc:
            from model_integrity import is_auth_or_network_error, force_redownload
            if not is_auth_or_network_error(exc):
                force_redownload(model_name)
                return _try_load()
            raise

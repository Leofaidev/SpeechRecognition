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

    # OPUS-MT models have a 512-token hard limit on input length.
    _CHUNK_TOKENS = 400  # headroom below the 512-token model limit

    def translate(self, texts: list[str]) -> list[str]:
        """Translate a list of strings.  Returns translated strings in order.

        Long texts are split into sentence-level chunks so that no chunk
        exceeds the model's token limit.  Translated chunks are rejoined
        with a space.  This prevents silent input truncation and avoids
        output being cut short by the model's default max-length cap.
        """
        if not texts:
            return []
        tokenizer, model = self._get_model()
        return [self._translate_one(tokenizer, model, t) for t in texts]

    def _translate_one(self, tokenizer, model, text: str) -> str:
        """Translate a single string, chunking if it exceeds the token limit."""
        import re
        token_ids = tokenizer.encode(text, add_special_tokens=False)
        if len(token_ids) <= self._CHUNK_TOKENS:
            return self._run_model(tokenizer, model, text)

        # Split on sentence boundaries and pack into ≤_CHUNK_TOKENS-token chunks.
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for sent in sentences:
            sent_len = len(tokenizer.encode(sent, add_special_tokens=False))
            if current and current_len + sent_len > self._CHUNK_TOKENS:
                chunks.append(" ".join(current))
                current, current_len = [sent], sent_len
            else:
                current.append(sent)
                current_len += sent_len
        if current:
            chunks.append(" ".join(current))

        return " ".join(self._run_model(tokenizer, model, c) for c in chunks)

    def _run_model(self, tokenizer, model, text: str) -> str:
        inputs = tokenizer([text], return_tensors="pt", padding=True,
                           truncation=True, max_length=512)
        output = model.generate(**inputs, max_new_tokens=512)
        return tokenizer.decode(output[0], skip_special_tokens=True)

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

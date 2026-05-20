"""Online translation via Google Translate free endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class TranslationServiceError(Exception):
    """Raised on HTTP failure, timeout, or malformed response."""


_GOOGLE_URL = "https://translate.googleapis.com/translate_a/single"
_TIMEOUT_SECONDS = 10


def translate(texts: list[str], source: str, target: str) -> list[str]:
    """Translate *texts* from *source* to *target* using Google Translate.

    Parameters
    ----------
    texts:
        Strings to translate.
    source:
        ISO 639-1 source language code (e.g. "en").  Use "auto" for detection.
    target:
        ISO 639-1 target language code.

    Returns
    -------
    Translated strings in the same order as input.

    Raises
    ------
    TranslationServiceError:
        On HTTP error (including 429 Too Many Requests), network timeout, or
        unparseable response.
    """
    if not texts:
        return []

    results: list[str] = []
    for text in texts:
        results.append(_translate_single(text, source, target))
    return results


def _translate_single(text: str, source: str, target: str) -> str:
    params = urllib.parse.urlencode({
        "client": "gtx",
        "sl": source,
        "tl": target,
        "dt": "t",
        "q": text,
    })
    url = f"{_GOOGLE_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise TranslationServiceError(
            f"Google Translate HTTP error {exc.code}: {exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise TranslationServiceError(
            f"Google Translate network error: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise TranslationServiceError("Google Translate request timed out") from exc

    try:
        data = json.loads(raw)
        parts = [segment[0] for segment in data[0] if segment[0]]
        return "".join(parts)
    except (json.JSONDecodeError, IndexError, TypeError, KeyError) as exc:
        raise TranslationServiceError(
            f"Unexpected Google Translate response format: {exc}"
        ) from exc

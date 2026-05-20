"""Unit tests for translation — CHK-38, 39, 40, 41."""

from unittest.mock import patch, MagicMock
import pytest

from config.store import ConfigStore
from translation.engine import TranslationEngine
from translation.google import TranslationServiceError
from translation.opus_mt import get_language_pair_info
from transcription.engine import TranscribedSegment


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_seg(text: str, bad_audio: bool = False) -> TranscribedSegment:
    return TranscribedSegment(
        speaker_id="Speaker 1",
        start=0.0, end=3.0,
        text=text, language="English", language_code="en",
        confidence=0.9, no_speech_prob=0.1,
        bad_audio=bad_audio,
    )


# ---------------------------------------------------------------------------
# CHK-38: TranslationServiceError on HTTP 429
# ---------------------------------------------------------------------------

def test_google_raises_on_http_429():
    import urllib.error
    from translation.google import translate

    mock_error = urllib.error.HTTPError(
        url="http://x", code=429, msg="Too Many Requests",
        hdrs=None, fp=None
    )
    with patch("urllib.request.urlopen", side_effect=mock_error):
        with pytest.raises(TranslationServiceError, match="429"):
            translate(["hello"], "en", "fi")


def test_google_error_does_not_fall_back():
    """Error propagates — no silent fallback to OPUS-MT."""
    import urllib.error
    from translation.google import translate

    mock_error = urllib.error.HTTPError(
        url="http://x", code=500, msg="Server Error",
        hdrs=None, fp=None
    )
    with patch("urllib.request.urlopen", side_effect=mock_error):
        with pytest.raises(TranslationServiceError):
            translate(["test"], "en", "fi")


# ---------------------------------------------------------------------------
# CHK-39: Translation applied AFTER substitution (engine ordering test)
# ---------------------------------------------------------------------------

def test_translation_receives_substituted_text():
    """The engine translates the text field, which should already be substituted."""
    config = ConfigStore(overrides={
        "translation_enabled": True,
        "translation_engine": "local",
        "source_language": "en",
        "target_language": "fi",
    })
    engine = TranslationEngine(config)

    # Inject a mock translator that records its input
    received: list[str] = []

    def fake_translate_local(texts, source, target):
        received.extend(texts)
        return texts  # return unchanged for this test

    engine._translate_local = fake_translate_local
    seg = make_seg("substituted_word says hello")
    engine.translate([seg])

    assert received[0] == "substituted_word says hello"


# ---------------------------------------------------------------------------
# CHK-40: quality_warning for English→Chinese; False for English→Finnish
# ---------------------------------------------------------------------------

def test_quality_warning_en_to_zh():
    info = get_language_pair_info("en", "zh")
    assert info.quality_warning is True


def test_quality_warning_en_to_zh_cn():
    info = get_language_pair_info("en", "zh-cn")
    assert info.quality_warning is True


def test_no_quality_warning_en_to_fi():
    info = get_language_pair_info("en", "fi")
    assert info.quality_warning is False


def test_no_quality_warning_en_to_de():
    info = get_language_pair_info("en", "de")
    assert info.quality_warning is False


# ---------------------------------------------------------------------------
# CHK-41: translation disabled → input text unchanged
# ---------------------------------------------------------------------------

def test_disabled_translation_returns_unchanged():
    config = ConfigStore(overrides={"translation_enabled": False})
    engine = TranslationEngine(config)
    seg = make_seg("Hello world")
    result = engine.translate([seg])
    assert result[0].text == "Hello world"


def test_disabled_translation_multiple_segments():
    config = ConfigStore(overrides={"translation_enabled": False})
    engine = TranslationEngine(config)
    segs = [make_seg("one"), make_seg("two"), make_seg("three")]
    result = engine.translate(segs)
    assert [s.text for s in result] == ["one", "two", "three"]


def test_disabled_translation_bad_audio_unchanged():
    config = ConfigStore(overrides={"translation_enabled": False})
    engine = TranslationEngine(config)
    seg = make_seg("XXXXX", bad_audio=True)
    result = engine.translate([seg])
    assert result[0].text == "XXXXX"


# ---------------------------------------------------------------------------
# enabled + bad_audio segments skipped
# ---------------------------------------------------------------------------

def test_bad_audio_segments_not_translated():
    config = ConfigStore(overrides={
        "translation_enabled": True,
        "translation_engine": "local",
        "source_language": "en",
        "target_language": "fi",
    })
    engine = TranslationEngine(config)

    translated_texts: list[str] = []

    def fake_translate_local(texts, source, target):
        translated_texts.extend(texts)
        return [t + "_translated" for t in texts]

    engine._translate_local = fake_translate_local

    segs = [
        make_seg("XXXXX", bad_audio=True),
        make_seg("Hello"),
    ]
    result = engine.translate(segs)

    assert result[0].text == "XXXXX"   # bad_audio unchanged
    assert result[1].text == "Hello_translated"
    assert "XXXXX" not in translated_texts

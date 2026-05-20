"""CHK-137 — Full pipeline with translation (Finnish → English).

Processes finnish_10s.wav with:
  - translation_enabled = True
  - translation_engine = "local" (Helsinki-NLP OPUS-MT)
  - source language auto-detected
  - target language = English

Expects:
- At least one segment with translated_text
- language prefix "Finnish:" in the TXT output

Requires faster-whisper tiny model AND Helsinki-NLP OPUS-MT models.
Pass --integration to run; first run will download OPUS-MT (~300 MB).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.integration.conftest import run_pipeline_sync

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.mark.integration
def test_finnish_wav_translated_to_english(tmp_path):
    """Process Finnish WAV; translated output segments contain English text.
    Language field shows 'Finnish'. (CHK-137)
    """
    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_formats": ["json"],
            "licence_accepted": False,
            "translation_enabled": True,
            "translation_engine": "local",
            "source_language": "auto",
            "target_language": "en",
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    runner = PipelineRunner(cfg)
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(FIXTURES / "finnish_10s.wav"),
        output_dir=out_dir,
        formats=["json"],
        timeout=300.0,
    )

    assert err is None, f"Pipeline error: {err}"
    assert result is not None and result.ok, f"Pipeline not ok: {result}"

    # At least one segment should be Finnish
    langs = {seg.language for seg in result.segments}
    assert "Finnish" in langs, (
        f"Expected Finnish language detection, got: {langs}"
    )

    # translated_text should differ from text (it's English)
    translated = [
        seg for seg in result.segments
        if seg.translated_text and seg.translated_text != seg.text
    ]
    assert translated, "Expected at least one segment with a translated_text"


@pytest.mark.integration
def test_translation_language_prefix_in_txt(tmp_path):
    """TXT output for a Finnish file includes 'Finnish:' language prefix."""
    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": True,
            "translation_engine": "local",
            "source_language": "auto",
            "target_language": "en",
            "output_fields": {
                "timestamp": True,
                "speaker": True,
                "language": True,
                "confidence": False,
                "text": True,
                "original_text": False,
            },
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    runner = PipelineRunner(cfg)
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(FIXTURES / "finnish_10s.wav"),
        output_dir=out_dir,
        formats=["txt"],
        timeout=300.0,
    )

    assert err is None and result is not None and result.ok

    txt_files = list(out_dir.glob("*_WSP.txt"))
    assert txt_files, "No TXT output file produced"
    content = txt_files[0].read_text(encoding="utf-8")
    assert "Finnish" in content, (
        f"Expected 'Finnish' language label in TXT output.\nContent:\n{content}"
    )

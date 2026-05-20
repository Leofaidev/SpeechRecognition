"""CHK-136, CHK-140, CHK-141, CHK-147 — File pipeline integration tests.

All tests use faster-whisper 'tiny' model and licence_accepted=False (no
pyannote diarization) so they are runnable without a HuggingFace account.

Pass --integration to run.  Models are downloaded automatically on first run.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

import pytest

from tests.integration.conftest import run_pipeline_sync

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_corrupt_wav(path: Path) -> Path:
    """Write a file with a .wav extension but invalid content."""
    path.write_bytes(b"NOTAWAVFILE\x00\x01\x02\x03")
    return path


# ---------------------------------------------------------------------------
# CHK-136 — Full pipeline (file): transcription + output files written
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_full_pipeline_file_txt_and_json(tmp_path):
    """Process english_10s.wav; verify TXT and JSON output files are written
    with at least one non-empty text segment. (CHK-136 — file pipeline)
    """
    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_folder": str(out_dir),
            "output_formats": ["txt", "json"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    runner = PipelineRunner(cfg)
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(FIXTURES / "english_10s.wav"),
        output_dir=out_dir,
        formats=["txt", "json"],
    )

    assert err is None, f"Pipeline error: {err}"
    assert result is not None and result.ok, f"Pipeline result not ok: {result}"

    txt_files = list(out_dir.glob("*_WSP.txt"))
    json_files = list(out_dir.glob("*_WSP.json"))
    assert len(txt_files) == 1, f"Expected 1 TXT file, got {txt_files}"
    assert len(json_files) == 1, f"Expected 1 JSON file, got {json_files}"

    # At least one segment should have transcribed text
    json_data = json.loads(json_files[0].read_text(encoding="utf-8"))
    texts = [seg.get("text", "") for seg in json_data.get("segments", [])]
    assert any(t.strip() for t in texts), "No transcribed text found in JSON output"


@pytest.mark.integration
def test_full_pipeline_language_detected(tmp_path):
    """English audio → language_code 'en' in at least one segment. (CHK-136)"""
    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_formats": ["json"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    runner = PipelineRunner(cfg)
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(FIXTURES / "english_10s.wav"),
        output_dir=out_dir,
        formats=["json"],
    )

    assert err is None and result is not None and result.ok

    # Segments attached to result carry language_code
    lang_codes = {seg.language_code for seg in result.segments}
    assert "en" in lang_codes, f"Expected 'en' in detected languages, got {lang_codes}"


# ---------------------------------------------------------------------------
# CHK-140 — Batch queue (3 files): all three produce output, no errors
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_batch_three_files_all_succeed(tmp_path):
    """Queue english_10s.wav, finnish_10s.wav, short_1s.wav → 3 output files,
    no failures reported. (CHK-140)
    """
    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    files = [
        str(FIXTURES / "english_10s.wav"),
        str(FIXTURES / "finnish_10s.wav"),
        str(FIXTURES / "short_1s.wav"),
    ]

    failed: list[str] = []
    batch_done = threading.Event()

    def _on_batch_done(f: list[str]) -> None:
        failed.extend(f)
        batch_done.set()

    runner = PipelineRunner(cfg)
    runner.start_batch(files, output_dir=out_dir, formats=["txt"],
                       on_batch_done=_on_batch_done)
    batch_done.wait(timeout=300.0)

    txt_files = list(out_dir.glob("*_WSP.txt"))
    assert len(txt_files) == 3, f"Expected 3 TXT files, got {[f.name for f in txt_files]}"
    assert failed == [], f"Unexpected failures: {failed}"


# ---------------------------------------------------------------------------
# CHK-141 — Batch queue with one bad file: good files still produce output
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_batch_with_one_corrupt_file(tmp_path):
    """Queue 3 files where file 2 is corrupt. Files 1 and 3 produce output;
    file 2 is reported as failed. (CHK-141)
    """
    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner

    out_dir = tmp_path / "out"
    corrupt = _make_corrupt_wav(tmp_path / "corrupt.wav")

    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    files = [
        str(FIXTURES / "english_10s.wav"),
        str(corrupt),
        str(FIXTURES / "short_1s.wav"),
    ]

    failed: list[str] = []
    batch_done = threading.Event()

    def _on_batch_done(f: list[str]) -> None:
        failed.extend(f)
        batch_done.set()

    runner = PipelineRunner(cfg)
    runner.start_batch(files, output_dir=out_dir, formats=["txt"],
                       on_batch_done=_on_batch_done)
    batch_done.wait(timeout=300.0)

    txt_files = list(out_dir.glob("*_WSP.txt"))
    assert len(txt_files) == 2, (
        f"Expected 2 TXT files (good files only), got {[f.name for f in txt_files]}"
    )
    assert len(failed) == 1, f"Expected exactly 1 failure, got {failed}"
    assert str(corrupt) in failed, f"Corrupt file not in failed list: {failed}"


# ---------------------------------------------------------------------------
# CHK-147 — No GPU: CPU-only processing produces output without crash
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_cpu_only_pipeline(tmp_path, monkeypatch):
    """Set CUDA_VISIBLE_DEVICES=-1; pipeline runs on CPU and produces output.
    (CHK-147)
    """
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "-1")

    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": False,  # force CPU
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    runner = PipelineRunner(cfg)
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(FIXTURES / "english_10s.wav"),
        output_dir=out_dir,
        formats=["txt"],
    )

    assert err is None, f"CPU-only pipeline raised an error: {err}"
    assert result is not None and result.ok
    assert len(list(out_dir.glob("*_WSP.txt"))) == 1

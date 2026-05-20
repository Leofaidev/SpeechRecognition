"""CHK-148 to CHK-153 — Performance benchmarks.

All benchmarks require faster-whisper models downloaded locally.
CHK-153 additionally requires pyannote.audio models (HF_TOKEN).

Pass --performance to run.

Targets from WorkPlan:
  CHK-148  CUDA 10-min WAV < 3 min total (diarization + transcription)
  CHK-149  CPU  10-min WAV < 15 min total
  CHK-150  Cold-start: import to GUI-ready < 10 s
  CHK-151  GUI responsiveness (manual — not tested here)
  CHK-152  Memory: 30-min WAV on CPU < 8 GB peak RAM
  CHK-153  Retrain 20 profiles on CUDA < 5 min
"""
from __future__ import annotations

import os
import time
import wave
from pathlib import Path

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Synthetic audio helpers
# ---------------------------------------------------------------------------

def _write_wav(path: Path, duration_sec: float, sr: int = 16_000) -> Path:
    """Generate a 440 Hz sine-wave WAV of the requested duration."""
    n = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    samples = (np.sin(2 * np.pi * 440 * t) * 0.4 * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    return path


@pytest.fixture(scope="module")
def wav_10min(tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("perf") / "bench_10min.wav"
    return _write_wav(p, 10 * 60)


@pytest.fixture(scope="module")
def wav_30min(tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("perf") / "bench_30min.wav"
    return _write_wav(p, 30 * 60)


# ---------------------------------------------------------------------------
# CHK-148 — CUDA 10-min WAV total pipeline time < 3 min
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_cuda_10min_under_3min(tmp_path, wav_10min):
    """Process a 10-minute WAV on CUDA (RTX 3060 Ti).
    Total wall time (diarization + transcription) must be < 180 seconds.
    (CHK-148)
    """
    import torch
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available — cannot run CHK-148")

    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner
    from tests.integration.conftest import run_pipeline_sync

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "medium",
            "gpu_enabled": True,
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    runner = PipelineRunner(cfg)
    t0 = time.perf_counter()
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(wav_10min),
        output_dir=out_dir,
        formats=["txt"],
        timeout=300.0,
    )
    elapsed = time.perf_counter() - t0

    assert err is None and result is not None and result.ok
    assert elapsed < 180.0, (
        f"CHK-148 FAILED: {elapsed:.1f}s exceeds 180s target for 10-min CUDA run"
    )


# ---------------------------------------------------------------------------
# CHK-149 — CPU 10-min WAV total pipeline time < 15 min
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_cpu_10min_under_15min(tmp_path, wav_10min, monkeypatch):
    """Process a 10-minute WAV on CPU only.
    Total wall time must be < 900 seconds. (CHK-149)
    """
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "-1")

    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner
    from tests.integration.conftest import run_pipeline_sync

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "medium",
            "gpu_enabled": False,
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    runner = PipelineRunner(cfg)
    t0 = time.perf_counter()
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(wav_10min),
        output_dir=out_dir,
        formats=["txt"],
        timeout=1200.0,
    )
    elapsed = time.perf_counter() - t0

    assert err is None and result is not None and result.ok
    assert elapsed < 900.0, (
        f"CHK-149 FAILED: {elapsed:.1f}s exceeds 900s target for 10-min CPU run"
    )


# ---------------------------------------------------------------------------
# CHK-150 — Cold-start: imports + ConfigStore ready < 10 s
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_cold_start_imports_under_10s():
    """Time the imports needed before the GUI can open.
    Target: < 10 seconds. (CHK-150)

    Note: this tests import time in the current process (already warmed up
    somewhat).  A true cold-start measurement should be done with a subprocess;
    this check acts as a CI-friendly proxy.
    """
    import importlib
    import sys

    # Remove cached modules so we get a fair timing for heavy imports
    for mod in list(sys.modules.keys()):
        if any(mod.startswith(p) for p in (
            "customtkinter", "faster_whisper", "gui", "config"
        )):
            sys.modules.pop(mod, None)

    t0 = time.perf_counter()
    importlib.import_module("config.store")
    importlib.import_module("gui.lang")
    importlib.import_module("customtkinter")
    elapsed = time.perf_counter() - t0

    assert elapsed < 10.0, (
        f"CHK-150 FAILED: heavy imports took {elapsed:.2f}s (target < 10s)"
    )


# ---------------------------------------------------------------------------
# CHK-152 — Memory: 30-min CPU pipeline < 8 GB peak RAM
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_memory_30min_cpu_under_8gb(tmp_path, wav_30min, monkeypatch):
    """Process a 30-minute WAV on CPU; peak RAM must stay below 8 GB.
    Uses tracemalloc for in-process measurement. (CHK-152)
    """
    import tracemalloc

    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "-1")

    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner
    from tests.integration.conftest import run_pipeline_sync

    out_dir = tmp_path / "out"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "medium",
            "gpu_enabled": False,
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    tracemalloc.start()
    runner = PipelineRunner(cfg)
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(wav_30min),
        output_dir=out_dir,
        formats=["txt"],
        timeout=1800.0,
    )
    _current, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert err is None and result is not None and result.ok

    peak_gb = peak_bytes / (1024 ** 3)
    assert peak_gb < 8.0, (
        f"CHK-152 FAILED: peak RAM {peak_gb:.2f} GB exceeds 8 GB target"
    )


# ---------------------------------------------------------------------------
# CHK-153 — Retrain 20 speaker profiles on CUDA < 5 min
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_retrain_20_profiles_under_5min(tmp_path):
    """Retrain embeddings for 20 synthetic voice profiles on CUDA.
    Total time must be < 300 seconds. (CHK-153)

    Requires pyannote.audio models (set HF_TOKEN env var).
    """
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not hf_token:
        pytest.skip("HF_TOKEN not set — pyannote models unavailable for CHK-153")

    import torch
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available — cannot run CHK-153")

    from audio.ingest import load
    from config.store import ConfigStore
    from library.storage import LibraryStorage
    from library.profile_creator import ProfileCreator
    from library.retrainer import Retrainer

    FIXTURES = Path(__file__).parent.parent / "fixtures"
    library_root = tmp_path / "library"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "medium",
            "gpu_enabled": True,
            "licence_accepted": True,
            "library_root": str(library_root),
        }
    )

    audio, sr = load(str(FIXTURES / "english_10s.wav"))
    storage = LibraryStorage(library_root)
    creator = ProfileCreator(storage)

    # Create 20 synthetic profiles (all use the same 10-s sample for speed)
    for i in range(20):
        creator.create(
            audio, sr,
            last=f"Speaker{i:02d}", first="", middle="", nickname="",
            organisation="", position="", note="",
        )

    retrainer = Retrainer(storage, cfg)
    t0 = time.perf_counter()
    summary = retrainer.retrain_all()
    elapsed = time.perf_counter() - t0

    assert summary.total == 20
    assert elapsed < 300.0, (
        f"CHK-153 FAILED: retraining 20 profiles took {elapsed:.1f}s (target < 300s)"
    )

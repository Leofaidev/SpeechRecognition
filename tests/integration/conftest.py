"""Shared fixtures and helpers for integration tests."""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="session")
def hf_token() -> str | None:
    """HuggingFace token from env; None if absent (pyannote tests skip)."""
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")


@pytest.fixture
def cfg(tmp_path):
    """ConfigStore with safe settings: tiny Whisper, no diarization, no translation."""
    from config.store import ConfigStore

    return ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_folder": str(tmp_path / "out"),
            "output_formats": ["txt"],
            "licence_accepted": False,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "library_root": str(tmp_path / "library"),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )


def run_pipeline_sync(
    runner,
    method: str,
    *args: Any,
    timeout: float = 300.0,
    **kwargs: Any,
) -> tuple[Any, str | None]:
    """Invoke runner.<method>(*args, **kwargs) and block until the pipeline finishes.

    Returns (PipelineResult | None, error_message | None).
    """
    done = threading.Event()
    box: dict[str, Any] = {}

    orig_done = runner._on_done
    orig_error = runner._on_error

    def _on_done(r: Any) -> None:
        box["result"] = r
        done.set()
        orig_done(r)

    def _on_error(e: str) -> None:
        box["error"] = e
        done.set()
        orig_error(e)

    runner._on_done = _on_done
    runner._on_error = _on_error

    getattr(runner, method)(*args, **kwargs)
    completed = done.wait(timeout=timeout)
    if not completed:
        box["error"] = f"Pipeline timed out after {timeout}s"

    return box.get("result"), box.get("error")

"""CHK-142 — Speaker identification from a voice profile.

Creates a voice profile for a speaker from a known audio sample, then
processes another sample from the same speaker and verifies the profile
name appears in the output instead of 'Speaker N'.

Requires:
- faster-whisper tiny model
- pyannote.audio models (HuggingFace account + licence acceptance)
- Set env var HF_TOKEN or HUGGINGFACE_TOKEN before running

Pass --integration to run.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.integration.conftest import run_pipeline_sync

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _skip_if_no_hf_token(hf_token):
    if not hf_token:
        pytest.skip(
            "HF_TOKEN / HUGGINGFACE_TOKEN env var not set — "
            "skipping pyannote-dependent speaker ID test"
        )


@pytest.mark.integration
def test_speaker_identified_from_profile(tmp_path, hf_token):
    """Profile created from two_speaker_30s.mp3; processing the same file should
    identify the registered speaker by name, not as 'Speaker N'. (CHK-142)
    """
    _skip_if_no_hf_token(hf_token)

    from audio.ingest import load
    from config.store import ConfigStore
    from gui.pipeline import PipelineRunner
    from library.storage import LibraryStorage
    from library.profile_creator import ProfileCreator

    library_root = tmp_path / "library"
    cfg = ConfigStore(
        overrides={
            "whisper_model": "tiny",
            "gpu_enabled": True,
            "output_formats": ["json"],
            "licence_accepted": True,
            "translation_enabled": False,
            "sessions_dir": str(tmp_path / "sessions"),
            "library_root": str(library_root),
            "dictionary_file": str(tmp_path / "dictionary.json"),
        }
    )

    # Create a voice profile named "TestSpeaker"
    audio, sr = load(str(FIXTURES / "two_speaker_30s.mp3"))
    storage = LibraryStorage(library_root)
    creator = ProfileCreator(storage)
    folder, _meta = creator.create(
        audio, sr,
        last="TestSpeaker", first="", middle="", nickname="",
        organisation="", position="", note="",
    )
    group_name = folder.name

    # Process the same audio with the profile group active
    out_dir = tmp_path / "out"
    runner = PipelineRunner(cfg)
    result, err = run_pipeline_sync(
        runner, "start_file",
        str(FIXTURES / "two_speaker_30s.mp3"),
        output_dir=out_dir,
        formats=["json"],
        speaker_group=group_name,
        timeout=300.0,
    )

    assert err is None, f"Pipeline error: {err}"
    assert result is not None and result.ok

    speaker_names = {seg.speaker_id for seg in result.segments}
    assert "TestSpeaker" in speaker_names, (
        f"Expected 'TestSpeaker' in speaker labels, got: {speaker_names}"
    )

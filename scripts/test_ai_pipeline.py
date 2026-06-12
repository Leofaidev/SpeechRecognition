#!/usr/bin/env python3
"""AI pipeline smoke test — verifies faster-whisper and pyannote work on this system.

Run from repo root:
    python3 scripts/test_ai_pipeline.py [--model tiny] [--hf-token TOKEN]

Inside Docker:
    docker run --gpus all --rm -it wsp-test python3 scripts/test_ai_pipeline.py
"""
from __future__ import annotations

import argparse
import struct
import sys
import wave
from io import BytesIO
from pathlib import Path

_PASS = "\033[32m✓\033[0m"
_FAIL = "\033[31m✗\033[0m"
_INFO = "\033[33m→\033[0m"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(label: str, ok: bool, detail: str = "") -> bool:
    sym = _PASS if ok else _FAIL
    print(f"  {sym}  {label}" + (f": {detail}" if detail else ""))
    return ok


def _make_silence_wav(duration_s: float = 3.0, sample_rate: int = 16000) -> bytes:
    """Return bytes of a minimal mono 16-bit WAV containing silence."""
    n = int(duration_s * sample_rate)
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n}h", *([0] * n)))
    return buf.getvalue()


def _save_tmp_wav(data: bytes) -> Path:
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.write(fd, data)
    os.close(fd)
    return Path(path)


# ---------------------------------------------------------------------------
# Test steps
# ---------------------------------------------------------------------------

def test_cuda(results: list) -> bool:
    print("\n[1] CUDA / GPU")
    try:
        import torch
        available = torch.cuda.is_available()
        _check("torch.cuda.is_available()", available)
        if available:
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                vram_gb = props.total_memory / 1024**3
                _check(f"  GPU {i}", True, f"{props.name}  {vram_gb:.1f} GB VRAM")
        else:
            print(f"  {_INFO}  Running on CPU — transcription will be slower")
        results.append(("CUDA available", available))
        return True  # non-fatal
    except ImportError as e:
        _check("torch import", False, str(e))
        results.append(("CUDA available", False))
        return False


def test_faster_whisper(model_size: str, results: list) -> bool:
    print(f"\n[2] faster-whisper (model={model_size})")
    try:
        import torch
        from faster_whisper import WhisperModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        _check("import faster_whisper", True)

        print(f"  {_INFO}  Loading model '{model_size}' on {device} …", flush=True)
        model = WhisperModel(model_size, device=device, compute_type=compute)
        _check("model loaded", True)

        wav_bytes = _make_silence_wav(3.0)
        tmp = _save_tmp_wav(wav_bytes)
        try:
            segs, info = model.transcribe(str(tmp), beam_size=1)
            segs = list(segs)
            _check("transcribe(silence)", True,
                   f"language={info.language!r}, {len(segs)} segment(s)")
        finally:
            tmp.unlink(missing_ok=True)

        results.append(("faster-whisper", True))
        return True
    except Exception as e:
        _check("faster-whisper", False, str(e))
        results.append(("faster-whisper", False))
        return False


def test_pyannote(hf_token: str | None, results: list) -> bool:
    print("\n[3] pyannote.audio (speaker diarization)")
    if not hf_token:
        print(f"  {_INFO}  --hf-token not supplied — skipping diarization test")
        print(f"  {_INFO}  Pass your HuggingFace token to test speaker identification")
        results.append(("pyannote (skipped)", None))
        return True

    try:
        import torch
        from pyannote.audio import Pipeline
        _check("import pyannote.audio", True)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  {_INFO}  Loading diarization pipeline on {device} …", flush=True)
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token,
        )
        import torch as _torch
        pipeline.to(_torch.device(device))
        _check("pipeline loaded", True)

        sr = 16000
        waveform = torch.zeros(1, sr * 5)  # 5 s mono silence, no file I/O
        output = pipeline({"waveform": waveform, "sample_rate": sr})
        # pyannote ≥3.x returns DiarizeOutput; annotation is in .speaker_diarization
        diarization = getattr(output, "speaker_diarization",
                              getattr(output, "diarization", output))
        segments = list(diarization.itertracks(yield_label=True))
        _check("diarize(silence)", True, f"{len(segments)} segment(s)")

        results.append(("pyannote", True))
        return True
    except Exception as e:
        _check("pyannote", False, str(e))
        results.append(("pyannote", False))
        return False


def test_ffmpeg(results: list) -> bool:
    print("\n[4] FFmpeg")
    import subprocess
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        line = r.stdout.splitlines()[0] if r.stdout else "?"
        _check("ffmpeg", r.returncode == 0, line.split("Copyright")[0].strip())
        results.append(("ffmpeg", r.returncode == 0))
        return r.returncode == 0
    except FileNotFoundError:
        _check("ffmpeg", False, "not found — install: sudo apt-get install ffmpeg")
        results.append(("ffmpeg", False))
        return False


def test_audio_ingest(results: list) -> bool:
    print("\n[5] audio.ingest (FFmpeg pipeline)")
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "platforms"))
        from audio.ingest import load
        _check("import audio.ingest", True)

        wav_bytes = _make_silence_wav(2.0)
        tmp = _save_tmp_wav(wav_bytes)
        try:
            audio, sr = load(str(tmp))
            _check("load(wav)", True, f"shape={audio.shape}  sr={sr}")
        finally:
            tmp.unlink(missing_ok=True)

        results.append(("audio.ingest", True))
        return True
    except Exception as e:
        _check("audio.ingest", False, str(e))
        results.append(("audio.ingest", False))
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="AI pipeline smoke test")
    parser.add_argument("--model", default="tiny",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper model size (default: tiny)")
    parser.add_argument("--hf-token", default="",
                        help="HuggingFace token for pyannote diarization test")
    args = parser.parse_args()

    print("=" * 60)
    print("  Speech Recognition Program — AI pipeline smoke test")
    print("=" * 60)
    print(f"  Python  {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")

    results: list[tuple[str, bool | None]] = []

    test_cuda(results)
    test_ffmpeg(results)
    test_audio_ingest(results)
    test_faster_whisper(args.model, results)
    test_pyannote(args.hf_token or None, results)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, v in results if v is True)
    failed = sum(1 for _, v in results if v is False)
    skipped = sum(1 for _, v in results if v is None)
    print(f"  Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

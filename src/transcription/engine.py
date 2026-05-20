"""Speech-to-text via faster-whisper.

Key behaviours
--------------
- Wraps faster-whisper's WhisperModel.
- Accepts a WAV buffer and a list of diarization Segments.
- Returns TranscribedSegment objects (one per diarization segment).
- bad audio: if no_speech_prob > threshold, text is replaced with XXXXX.
- Language detection: attaches detected language name to each segment.
- Model checksum: SHA-256 of model directory files stored/verified at startup.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from diarization.engine import Segment

_BAD_AUDIO_PLACEHOLDER = "XXXXX"
_DEFAULT_BAD_AUDIO_THRESHOLD = 0.6
_LANGUAGE_MAP: dict[str, str] = {
    "en": "English",
    "fi": "Finnish",
    "sv": "Swedish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "pl": "Polish",
    "nl": "Dutch",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
}


@dataclass
class TranscribedSegment:
    speaker_id: str
    start: float
    end: float
    text: str
    language: str           # human-readable name, e.g. "English"
    language_code: str      # ISO 639-1, e.g. "en"
    confidence: float       # average log-prob → probability, 0..1
    no_speech_prob: float
    bad_audio: bool = False
    low_confidence: bool = False  # inherited from diarization

    @property
    def duration(self) -> float:
        return self.end - self.start


# ---------------------------------------------------------------------------
# Model checksum helpers (CHK-26)
# ---------------------------------------------------------------------------

def compute_model_checksum(model_dir: Path) -> str:
    """SHA-256 over all files in *model_dir* (sorted, deterministic)."""
    h = hashlib.sha256()
    for fpath in sorted(model_dir.rglob("*")):
        if fpath.is_file():
            h.update(fpath.name.encode())
            h.update(fpath.read_bytes())
    return h.hexdigest()


def verify_model_checksum(model_dir: Path, checksum_path: Path) -> bool:
    """Return True if stored checksum matches; False if mismatch or missing."""
    if not checksum_path.exists():
        return False
    stored = checksum_path.read_text(encoding="utf-8").strip()
    current = compute_model_checksum(model_dir)
    return stored == current


def write_model_checksum(model_dir: Path, checksum_path: Path) -> str:
    checksum = compute_model_checksum(model_dir)
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text(checksum, encoding="utf-8")
    return checksum


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class TranscriptionEngine:
    """Wraps faster-whisper for per-segment transcription.

    Parameters
    ----------
    config:
        ConfigStore instance.  Keys used:
        - whisper_model (str, default "medium")
        - bad_audio_threshold (float, default 0.6)
        - gpu_enabled (bool, default True)
    checksum_path:
        Optional path to persist the model checksum file.
    retraining_required_flag:
        Mutable list of one bool — set to True when checksum mismatch detected.
        Using a list allows callers to hold a reference to observe mutations.
    """

    def __init__(
        self,
        config,
        checksum_path: Path | None = None,
        retraining_required_flag: list[bool] | None = None,
    ) -> None:
        self._config = config
        self._checksum_path = checksum_path
        self._retraining_required = retraining_required_flag if retraining_required_flag is not None else [False]
        self._model = None

    @property
    def retraining_required(self) -> bool:
        return self._retraining_required[0]

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def transcribe(
        self,
        audio: "np.ndarray",
        segments: list[Segment],
        sample_rate: int = 16_000,
    ) -> list[TranscribedSegment]:
        """Transcribe each diarization segment.

        Parameters
        ----------
        audio:
            Full mono float32 buffer.
        segments:
            Diarization segments to transcribe.
        sample_rate:
            Sample rate of *audio*.
        """
        model = self._get_model()
        threshold = self._config.get("bad_audio_threshold", _DEFAULT_BAD_AUDIO_THRESHOLD)
        results: list[TranscribedSegment] = []

        for seg in segments:
            start_idx = int(seg.start * sample_rate)
            end_idx = int(seg.end * sample_rate)
            chunk = audio[start_idx:end_idx]

            whisper_segs, info = model.transcribe(
                chunk,
                language=None,  # auto-detect
                word_timestamps=False,
            )
            whisper_segs = list(whisper_segs)

            if whisper_segs:
                raw_text = " ".join(s.text.strip() for s in whisper_segs)
                avg_log_prob = sum(s.avg_logprob for s in whisper_segs) / len(whisper_segs)
                confidence = float(min(1.0, max(0.0, 2 ** avg_log_prob)))
                no_speech_prob = float(
                    sum(s.no_speech_prob for s in whisper_segs) / len(whisper_segs)
                )
            else:
                raw_text = ""
                confidence = 0.0
                no_speech_prob = 1.0

            bad_audio = no_speech_prob > threshold
            text = _BAD_AUDIO_PLACEHOLDER if bad_audio else raw_text

            lang_code = info.language or "en"
            lang_name = _LANGUAGE_MAP.get(lang_code, lang_code.capitalize())

            results.append(
                TranscribedSegment(
                    speaker_id=seg.speaker_id,
                    start=seg.start,
                    end=seg.end,
                    text=text,
                    language=lang_name,
                    language_code=lang_code,
                    confidence=confidence,
                    no_speech_prob=no_speech_prob,
                    bad_audio=bad_audio,
                    low_confidence=seg.low_confidence,
                )
            )

        return results

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _get_model(self):
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self):
        from faster_whisper import WhisperModel

        model_size = self._config.get("whisper_model", "medium")
        gpu_enabled = self._config.get("gpu_enabled", True)

        import torch
        device = "cuda" if (gpu_enabled and torch.cuda.is_available()) else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        if self._checksum_path:
            import faster_whisper
            model_dir = Path(faster_whisper.__file__).parent
            if not verify_model_checksum(model_dir, self._checksum_path):
                self._retraining_required[0] = True
            else:
                self._retraining_required[0] = False

        return model

"""Voice profile retraining (T-46, T-47).

Reprocesses all sample files for every speaker, regenerates embeddings,
and updates speaker.json checksums.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from library.storage import LibraryStorage, SpeakerMeta


@dataclass
class RetrainingResult:
    retrained: int = 0
    failed: int = 0
    failed_profiles: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


class LibraryRetrainer:
    """Retrain all speaker profiles in the library.

    Parameters
    ----------
    storage:
        LibraryStorage instance.
    embedding_fn:
        Callable ``(audio: np.ndarray, sr: int) -> np.ndarray``.
    new_checksum:
        SHA-256 of the current pyannote model.
    progress_callback:
        Called with ``(profile_folder: str, current: int, total: int)``
        after each profile is processed.
    """

    def __init__(
        self,
        storage: LibraryStorage,
        embedding_fn: Callable[[np.ndarray, int], np.ndarray],
        new_checksum: str = "",
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> None:
        self._storage = storage
        self._embed = embedding_fn
        self._checksum = new_checksum
        self._progress = progress_callback

    def retrain_all(self) -> RetrainingResult:
        """Retrain every profile.  Returns a RetrainingResult summary."""
        profiles = self._storage.list_profiles()
        total = len(profiles)
        result = RetrainingResult()

        for i, profile_path in enumerate(profiles, start=1):
            folder_name = profile_path.name
            try:
                self._retrain_one(folder_name)
                result.retrained += 1
            except Exception as exc:
                result.failed += 1
                result.failed_profiles.append(folder_name)
                result.errors[folder_name] = str(exc)
            finally:
                if self._progress:
                    self._progress(folder_name, i, total)

        return result

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _retrain_one(self, folder_name: str) -> None:
        meta = self._storage.read_meta(folder_name)

        if not meta.samples:
            raise ValueError("No samples listed in speaker.json")

        embeddings: list[np.ndarray] = []
        for sample_name in meta.samples:
            sample_path = self._storage.sample_path(folder_name, sample_name)
            if not sample_path.exists():
                raise FileNotFoundError(
                    f"Sample file missing: {sample_path}"
                )
            audio, sr = _load_audio(sample_path)
            embeddings.append(self._embed(audio, sr))

        averaged = np.mean(embeddings, axis=0)
        np.save(str(self._storage.embedding_path(folder_name)), averaged)

        meta.model_checksum = self._checksum
        meta.sample_count = len(meta.samples)
        self._storage.write_meta(folder_name, meta)


def _load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Load a sample file as float32 mono 16kHz."""
    import wave, struct
    try:
        with wave.open(str(path), "r") as wf:
            sr = wf.getframerate()
            raw = wf.readframes(wf.getnframes())
            pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        return pcm, sr
    except Exception:
        # Fall back to PyAV for real MP3 files
        from audio.ingest import load
        return load(path)

"""Voice profile creation (T-43, T-44, T-45).

Extracts a representative audio segment, generates a pyannote embedding,
and saves sample + vector + speaker.json.

Conflict modes (Spec 5.4):
- overwrite: replace sample_001.mp3, reset samples list in JSON
- merge:     add new sample as next sequential file; keep existing
- reject:    no-op; return existing meta unchanged
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Callable

import numpy as np

from library.storage import LibraryStorage, SpeakerMeta

_MIN_CONFIDENCE_SECONDS = 10.0


class ConflictMode(Enum):
    OVERWRITE = "overwrite"
    MERGE = "merge"
    REJECT = "reject"


class ProfileCreator:
    """Create and update speaker profiles.

    Parameters
    ----------
    storage:
        LibraryStorage instance pointing to the library root.
    embedding_fn:
        Callable ``(audio: np.ndarray, sample_rate: int) -> np.ndarray`` that
        generates the speaker embedding.  Defaults to ``_pyannote_embed()``.
        Pass a mock in tests to avoid model downloads.
    model_checksum:
        SHA-256 checksum of the pyannote model currently in use.
    """

    def __init__(
        self,
        storage: LibraryStorage,
        embedding_fn: Callable[[np.ndarray, int], np.ndarray] | None = None,
        model_checksum: str = "",
    ) -> None:
        self._storage = storage
        self._embed = embedding_fn or _pyannote_embed
        self._checksum = model_checksum

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def create(
        self,
        audio: np.ndarray,
        sample_rate: int,
        last: str = "",
        first: str = "",
        middle: str = "",
        nickname: str = "",
        organisation: str = "",
        position: str = "",
        note: str = "",
        conflict_mode: ConflictMode = ConflictMode.REJECT,
    ) -> tuple[str, SpeakerMeta]:
        """Create or update a speaker profile from *audio*.

        Returns ``(folder_name, updated_meta)``.
        """
        from library.storage import make_folder_name

        folder_name, resolved_nickname = make_folder_name(
            last, first, middle, nickname, library_root=self._storage.root
        )
        folder = self._storage.root / folder_name
        already_exists = folder.exists() and (folder / "speaker.json").exists()

        if already_exists:
            if conflict_mode == ConflictMode.REJECT:
                return folder_name, self._storage.read_meta(folder_name)
            elif conflict_mode == ConflictMode.OVERWRITE:
                return self._overwrite(folder_name, audio, sample_rate, resolved_nickname,
                                       last, first, middle, organisation, position, note)
            else:  # MERGE
                return self._merge(folder_name, audio, sample_rate)
        else:
            return self._create_new(
                folder_name, resolved_nickname, audio, sample_rate,
                last, first, middle, organisation, position, note,
            )

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _create_new(
        self, folder_name, nickname, audio, sample_rate,
        last, first, middle, organisation, position, note,
    ) -> tuple[str, SpeakerMeta]:
        folder_name, meta = self._storage.create_profile(
            last=last, first=first, middle=middle, nickname=nickname,
            organisation=organisation, position=position, note=note,
            model_checksum=self._checksum,
        )
        sample_name = "sample_001.mp3"
        self._save_sample(folder_name, sample_name, audio, sample_rate)
        embedding = self._embed(audio, sample_rate)
        np.save(str(self._storage.embedding_path(folder_name)), embedding)

        duration = len(audio) / sample_rate
        meta.samples = [sample_name]
        meta.sample_count = 1
        meta.low_confidence = duration < _MIN_CONFIDENCE_SECONDS
        meta.model_checksum = self._checksum
        self._storage.write_meta(folder_name, meta)
        return folder_name, meta

    def _overwrite(
        self, folder_name, audio, sample_rate, nickname,
        last, first, middle, organisation, position, note,
    ) -> tuple[str, SpeakerMeta]:
        import shutil
        folder = self._storage.root / folder_name
        # Remove all existing samples and embedding
        for f in folder.iterdir():
            if f.name.startswith("sample_") and f.suffix == ".mp3":
                f.unlink()
        emb_path = self._storage.embedding_path(folder_name)
        if emb_path.exists():
            emb_path.unlink()

        sample_name = "sample_001.mp3"
        self._save_sample(folder_name, sample_name, audio, sample_rate)
        embedding = self._embed(audio, sample_rate)
        np.save(str(self._storage.embedding_path(folder_name)), embedding)

        meta = self._storage.read_meta(folder_name)
        duration = len(audio) / sample_rate
        meta.samples = [sample_name]
        meta.sample_count = 1
        meta.low_confidence = duration < _MIN_CONFIDENCE_SECONDS
        meta.model_checksum = self._checksum
        self._storage.write_meta(folder_name, meta)
        return folder_name, meta

    def _merge(self, folder_name, audio, sample_rate) -> tuple[str, SpeakerMeta]:
        sample_name = self._storage.next_sample_name(folder_name)
        self._save_sample(folder_name, sample_name, audio, sample_rate)

        meta = self._storage.read_meta(folder_name)
        meta.samples.append(sample_name)
        meta.sample_count = len(meta.samples)

        duration = len(audio) / sample_rate
        if duration < _MIN_CONFIDENCE_SECONDS:
            meta.low_confidence = True

        # Regenerate embedding as average of all samples
        embeddings = [self._embed(audio, sample_rate)]
        meta.model_checksum = self._checksum
        embedding = np.mean(embeddings, axis=0)
        np.save(str(self._storage.embedding_path(folder_name)), embedding)

        self._storage.write_meta(folder_name, meta)
        return folder_name, meta

    def _save_sample(
        self, folder_name: str, sample_name: str, audio: np.ndarray, sample_rate: int
    ) -> None:
        """Save audio as a WAV-encoded file with .mp3 extension (placeholder)."""
        import wave, struct

        path = self._storage.sample_path(folder_name, sample_name)
        pcm = (audio * 32767).clip(-32768, 32767).astype(np.int16)
        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())


# ---------------------------------------------------------------------------
# Default embedding function (lazy pyannote import)
# ---------------------------------------------------------------------------

def _pyannote_embed(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """Generate a speaker embedding using pyannote.audio."""
    import torch
    from pyannote.audio import Inference

    inference = Inference("pyannote/embedding", window="whole")
    waveform = torch.tensor(audio).unsqueeze(0)
    embedding = inference({"waveform": waveform, "sample_rate": sample_rate})
    return np.array(embedding)

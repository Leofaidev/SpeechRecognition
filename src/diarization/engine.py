"""Speaker diarization via pyannote.audio.

Key behaviours
--------------
- If licence_accepted is False in config, raises LicenceNotAcceptedError and all
  segments are returned with speaker_id="Unknown".
- Speaker IDs from pyannote are mapped to sequential "Speaker N" labels when they
  are not present in the active library group.
- Segments shorter than 10 seconds receive low_confidence=True.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    start: float      # seconds
    end: float        # seconds
    speaker_id: str
    low_confidence: bool = False

    @property
    def duration(self) -> float:
        return self.end - self.start


class LicenceNotAcceptedError(Exception):
    """Raised when the HuggingFace pyannote licence has not been accepted."""


# ---------------------------------------------------------------------------
# Speaker numbering helper
# ---------------------------------------------------------------------------

class SpeakerNumberer:
    """Maps raw pyannote speaker tokens to sequential 'Speaker N' labels.

    The mapping resets on each new session (create a new instance).
    If a speaker token is already in *known_speakers*, it passes through
    unchanged (used when the active library group contains named profiles).
    """

    def __init__(self, known_speakers: set[str] | None = None) -> None:
        self._known: set[str] = known_speakers or set()
        self._mapping: dict[str, str] = {}
        self._counter: int = 0

    def label(self, raw_id: str) -> str:
        if raw_id in self._known:
            return raw_id
        if raw_id not in self._mapping:
            self._counter += 1
            self._mapping[raw_id] = f"Speaker {self._counter}"
        return self._mapping[raw_id]

    def reset(self) -> None:
        self._mapping.clear()
        self._counter = 0


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

_MIN_CONFIDENCE_SECONDS = 10.0
_DEFAULT_MODEL = "pyannote/speaker-diarization-3.1"


class DiarizationEngine:
    """Wraps pyannote.audio for speaker diarization.

    Parameters
    ----------
    config:
        ConfigStore instance.  Must have ``licence_accepted`` and optionally
        ``huggingface_token`` keys.
    known_speakers:
        Set of speaker names already in the active library group; these
        identifiers pass through the numberer unchanged.
    """

    def __init__(self, config, known_speakers: set[str] | None = None) -> None:
        self._config = config
        self._numberer = SpeakerNumberer(known_speakers)
        self._pipeline = None

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def start_session(self) -> None:
        """Reset speaker numbering for a new session."""
        self._numberer.reset()

    def diarize(
        self,
        audio: "np.ndarray",  # noqa: F821 — avoid circular import at module level
        sample_rate: int = 16_000,
    ) -> list[Segment]:
        """Run diarization on *audio*.

        Parameters
        ----------
        audio:
            Mono float32 numpy array.
        sample_rate:
            Sample rate of *audio*.

        Returns
        -------
        List of Segment objects with speaker IDs and confidence flags.

        Raises
        ------
        LicenceNotAcceptedError:
            If the HuggingFace licence has not been accepted in config.
        """
        if not self._config.get("licence_accepted", False):
            raise LicenceNotAcceptedError(
                "HuggingFace pyannote licence not accepted. "
                "Enable diarization in Settings to accept the licence."
            )

        pipeline = self._get_pipeline()
        return self._run_pipeline(pipeline, audio, sample_rate)

    def diarize_or_unknown(
        self,
        audio: "np.ndarray",
        sample_rate: int = 16_000,
    ) -> list[Segment]:
        """Like diarize() but catches LicenceNotAcceptedError.

        Returns a single segment spanning the full audio with
        speaker_id="Unknown" if the licence is not accepted.
        """
        try:
            return self.diarize(audio, sample_rate)
        except LicenceNotAcceptedError:
            duration = len(audio) / sample_rate
            return [Segment(start=0.0, end=duration, speaker_id="Unknown")]

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _get_pipeline(self):
        if self._pipeline is None:
            self._pipeline = self._load_pipeline()
        return self._pipeline

    def _load_pipeline(self):
        from pyannote.audio import Pipeline

        token = self._config.get("huggingface_token", None)
        kwargs = {"token": token} if token else {}

        def _try_load():
            return Pipeline.from_pretrained(_DEFAULT_MODEL, **kwargs)

        try:
            pipeline = _try_load()
        except Exception as exc:
            from model_integrity import is_auth_or_network_error, force_redownload
            if not is_auth_or_network_error(exc):
                # Possibly corrupted cache — force a fresh download and retry
                force_redownload(_DEFAULT_MODEL, token=token)
                try:
                    pipeline = _try_load()
                except Exception as retry_exc:
                    self._raise_pipeline_load_error(retry_exc)
            else:
                self._raise_pipeline_load_error(exc)

        import torch
        if self._config.get("gpu_enabled", True) and torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))

        return pipeline

    def _raise_pipeline_load_error(self, exc: Exception) -> None:
        import re
        msg = str(exc)
        m = re.search(r"pyannote/[\w.-]+", msg)
        blocked = m.group(0) if m else "a required model"
        raise RuntimeError(
            f"Speaker diarization model could not be loaded.\n\n"
            f"Access was denied for: {blocked}\n\n"
            f"Steps to fix:\n"
            f"  1. Log in at huggingface.co\n"
            f"  2. Visit huggingface.co/{blocked} and click "
            f"'Agree and access repository'\n"
            f"  3. Restart the application\n\n"
            f"(All pyannote models must be approved separately.)"
        ) from exc

    def _apply_clustering_params(self, pipeline) -> None:
        threshold = self._config.get("pyannote_clustering_threshold", None)
        if threshold is None:
            return
        try:
            pipeline.clustering.threshold = float(threshold)
        except AttributeError:
            try:
                pipeline._clustering.threshold = float(threshold)
            except AttributeError:
                pass

    def _run_pipeline(self, pipeline, audio, sample_rate: int) -> list[Segment]:
        import torch

        self._apply_clustering_params(pipeline)

        waveform = torch.tensor(audio).unsqueeze(0)  # (1, samples)
        input_dict = {"waveform": waveform, "sample_rate": sample_rate}

        max_spk = self._config.get("pyannote_max_speakers", 0)
        call_kwargs: dict = {}
        if max_spk and int(max_spk) > 0:
            call_kwargs["max_speakers"] = int(max_spk)

        try:
            output = pipeline(input_dict, **call_kwargs)
        except TypeError:
            output = pipeline(input_dict)
        # pyannote ≥ 3.3 returns DiarizeOutput; extract the Annotation from it.
        diarization = getattr(output, "speaker_diarization",
                              getattr(output, "diarization", output))

        segments: list[Segment] = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            labeled = self._numberer.label(speaker)
            low_conf = (turn.end - turn.start) < _MIN_CONFIDENCE_SECONDS
            segments.append(
                Segment(
                    start=turn.start,
                    end=turn.end,
                    speaker_id=labeled,
                    low_confidence=low_conf,
                )
            )

        return segments

"""Load audio files (MP3, WAV, MP4, AVI) and return a normalised mono 16 kHz float32 buffer.

Uses PyAV (bundled FFmpeg) so no system-level FFmpeg installation is required.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".mp4", ".avi"}
_TARGET_SAMPLE_RATE = 16_000


def load(path: str | Path) -> tuple[np.ndarray, int]:
    """Load an audio file and return ``(samples, sample_rate)``.

    Parameters
    ----------
    path:
        File to load.  Accepted formats: MP3, WAV, MP4, AVI.

    Returns
    -------
    samples:
        Mono float32 numpy array normalised to ``[-1.0, 1.0]``.
    sample_rate:
        Always ``16000``.

    Raises
    ------
    FileNotFoundError:
        If *path* does not exist.
    ValueError:
        If the file extension is not in the supported set.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    ext = path.suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format '{ext}'. "
            f"Supported formats: {sorted(_SUPPORTED_EXTENSIONS)}"
        )

    return _load_with_av(path)


def _load_with_av(path: Path) -> tuple[np.ndarray, int]:
    import av  # imported lazily; PyAV bundles its own FFmpeg

    frames: list[np.ndarray] = []

    with av.open(str(path)) as container:
        # Locate the first audio stream
        audio_streams = [s for s in container.streams if s.type == "audio"]
        if not audio_streams:
            raise ValueError(f"No audio stream found in '{path}'")

        resampler = av.AudioResampler(
            format="fltp",  # float32 planar
            layout="mono",
            rate=_TARGET_SAMPLE_RATE,
        )

        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                # shape: (channels, samples) — mono so channels=1
                arr = resampled.to_ndarray()
                frames.append(arr[0])  # first (only) channel

        # flush resampler
        for resampled in resampler.resample(None):
            arr = resampled.to_ndarray()
            frames.append(arr[0])

    if not frames:
        return np.zeros(0, dtype=np.float32), _TARGET_SAMPLE_RATE

    samples = np.concatenate(frames).astype(np.float32)
    return samples, _TARGET_SAMPLE_RATE

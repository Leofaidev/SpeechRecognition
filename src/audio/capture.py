"""Microphone capture with 5-hour stream-splitting support."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

_SAMPLE_RATE = 16_000
_CHANNELS = 1
_CHUNK = 1024
_FORMAT_WIDTH = 2  # int16 → 2 bytes
_MAX_STREAM_SECONDS = 5 * 3600  # 5 hours


@dataclass
class CaptureSession:
    """Holds accumulated audio for one recording session."""

    sample_rate: int = _SAMPLE_RATE
    _buffers: list[np.ndarray] = field(default_factory=list, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def append(self, chunk: np.ndarray) -> None:
        with self._lock:
            self._buffers.append(chunk)

    def get_audio(self) -> np.ndarray:
        with self._lock:
            if not self._buffers:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(self._buffers).astype(np.float32)

    @property
    def duration_seconds(self) -> float:
        with self._lock:
            total_samples = sum(len(b) for b in self._buffers)
        return total_samples / self.sample_rate


class Capture:
    """Open a pyaudio input stream and record until ``stop()`` is called.

    Parameters
    ----------
    device_id:
        pyaudio device index.  ``None`` uses the system default.
    on_split:
        Optional callback called with the completed ``CaptureSession`` each time
        a 5-hour boundary is crossed.  The recorder immediately starts a new
        session; speaker numbering is NOT reset (handled by the caller).
    """

    def __init__(
        self,
        device_id: int | None = None,
        on_split: Callable[[CaptureSession], None] | None = None,
    ) -> None:
        self._device_id = device_id
        self._on_split = on_split
        self._session = CaptureSession()
        self._stream = None
        self._pa = None
        self._running = False

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        import pyaudio

        self._pa = pyaudio.PyAudio()
        self._running = True
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=_CHANNELS,
            rate=_SAMPLE_RATE,
            input=True,
            input_device_index=self._device_id,
            frames_per_buffer=_CHUNK,
            stream_callback=self._callback,
        )
        self._stream.start_stream()

    def stop(self) -> CaptureSession:
        """Stop recording and return the current session."""
        self._running = False
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pa is not None:
            self._pa.terminate()
            self._pa = None
        return self._session

    @property
    def current_session(self) -> CaptureSession:
        return self._session

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _callback(self, in_data, frame_count, time_info, status_flags):
        import pyaudio

        if not self._running:
            return (None, pyaudio.paComplete)

        chunk = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
        self._session.append(chunk)

        if self._session.duration_seconds >= _MAX_STREAM_SECONDS:
            completed = self._session
            self._session = CaptureSession()
            if self._on_split is not None:
                threading.Thread(
                    target=self._on_split, args=(completed,), daemon=True
                ).start()

        return (None, pyaudio.paContinue)


# ---------------------------------------------------------------------------
# Pure stream-splitting utility (unit-testable without pyaudio)
# ---------------------------------------------------------------------------

def split_at_boundary(
    audio: np.ndarray,
    sample_rate: int,
    max_seconds: float = _MAX_STREAM_SECONDS,
) -> list[np.ndarray]:
    """Split *audio* into chunks of at most *max_seconds* each.

    Parameters
    ----------
    audio:
        1-D float32 array of audio samples.
    sample_rate:
        Samples per second.
    max_seconds:
        Maximum duration of each chunk in seconds.

    Returns
    -------
    list of numpy arrays, each at most ``max_seconds`` long.
    The last chunk may be shorter.  Returns a list with one element if the
    audio fits in a single chunk.
    """
    max_samples = int(max_seconds * sample_rate)
    if max_samples <= 0:
        raise ValueError("max_seconds must be positive")

    chunks: list[np.ndarray] = []
    offset = 0
    while offset < len(audio):
        chunks.append(audio[offset : offset + max_samples])
        offset += max_samples

    if not chunks:
        return [audio]
    return chunks

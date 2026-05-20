"""Copy transcription output to the Windows clipboard.

Per Spec 8.1.c: clipboard output is only available for microphone input.
Calling write() with source_type="file" raises ClipboardNotAvailableError.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transcription.engine import TranscribedSegment


class ClipboardNotAvailableError(Exception):
    """Raised when clipboard output is requested for non-microphone input."""


def write(segments: list["TranscribedSegment"], source_type: str) -> None:
    """Copy segment text to the clipboard.

    Parameters
    ----------
    segments:
        Transcribed segments to copy.
    source_type:
        "microphone" or "file".  Only "microphone" is allowed.

    Raises
    ------
    ClipboardNotAvailableError:
        If *source_type* is not "microphone".
    """
    if source_type != "microphone":
        raise ClipboardNotAvailableError(
            f"Clipboard output is only available for microphone input, "
            f"not for source_type='{source_type}'. "
            "(Spec 8.1.c)"
        )

    text = "\n\n".join(seg.text for seg in segments)
    _copy_to_clipboard(text)


def _copy_to_clipboard(text: str) -> None:
    """Copy *text* to the system clipboard using pyperclip or ctypes fallback."""
    try:
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        _ctypes_copy(text)


def _ctypes_copy(text: str) -> None:
    import ctypes
    import ctypes.wintypes

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    encoded = (text + "\x00").encode("utf-16-le")
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    ptr = kernel32.GlobalLock(h_mem)
    ctypes.memmove(ptr, encoded, len(encoded))
    kernel32.GlobalUnlock(h_mem)

    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    user32.SetClipboardData(CF_UNICODETEXT, h_mem)
    user32.CloseClipboard()

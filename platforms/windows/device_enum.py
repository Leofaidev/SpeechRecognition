from __future__ import annotations

from platforms.base.device_enum import DeviceEnumBase, DeviceInfo, DeviceType

# Substrings (lowercase) identifying non-capture categories to exclude.
_EXCLUDE_PATTERNS = (
    "microsoft sound mapper",
    "primary sound capture",
    "stereo mix",
    "стерео микшер",        # Stereo Mix (Russian)
    "line in",
    "лин. вход",            # Line In (Russian)
    "линейный вход",        # Line Input (Russian)
    "aux",
    "virtual microphone",
    "intelligo vac",
    "splitcam",             # SplitCam virtual audio mixer
)


class DeviceEnum(DeviceEnumBase):

    def list_devices(self) -> list[DeviceInfo]:
        import pyaudio
        pa = pyaudio.PyAudio()
        try:
            wasapi_idx = _wasapi_host_api_index(pa)
            if wasapi_idx is not None:
                devices = _list_wasapi_devices(pa, wasapi_idx)
            else:
                devices = _list_mme_devices(pa)
        finally:
            pa.terminate()
        return devices


# ---------------------------------------------------------------------------

def _wasapi_host_api_index(pa) -> int | None:
    import pyaudio
    for i in range(pa.get_host_api_count()):
        if pa.get_host_api_info_by_index(i)["type"] == pyaudio.paWASAPI:
            return i
    return None


def _list_wasapi_devices(pa, host_api_index: int) -> list[DeviceInfo]:
    api_info = pa.get_host_api_info_by_index(host_api_index)
    devices: list[DeviceInfo] = []
    for j in range(api_info["deviceCount"]):
        dev = pa.get_device_info_by_host_api_device_index(host_api_index, j)
        if dev["maxInputChannels"] <= 0:
            continue
        name = _fix_name_encoding(dev["name"])
        if _should_exclude(name):
            continue
        devices.append(DeviceInfo(
            id=dev["index"],
            name=name,
            device_type=DeviceType.MICROPHONE,
            channel_count=int(dev["maxInputChannels"]),
            sample_rate=float(dev["defaultSampleRate"]),
        ))
    return devices


def _list_mme_devices(pa) -> list[DeviceInfo]:
    """Fallback when WASAPI is absent: all host APIs, deduplicated by name."""
    seen: set[str] = set()
    devices: list[DeviceInfo] = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] <= 0:
            continue
        name = _fix_name_encoding(info["name"])
        if _should_exclude(name) or name in seen:
            continue
        seen.add(name)
        devices.append(DeviceInfo(
            id=i,
            name=name,
            device_type=DeviceType.MICROPHONE,
            channel_count=int(info["maxInputChannels"]),
            sample_rate=float(info["defaultSampleRate"]),
        ))
    return devices


def _should_exclude(name: str) -> bool:
    low = name.lower()
    return any(pat in low for pat in _EXCLUDE_PATTERNS)


def _fix_name_encoding(name: str) -> str:
    """Reverse PyAudio's WASAPI double-encoding on Windows.

    PyAudio receives device names from Windows as UTF-8 bytes but decodes
    them using the system ANSI code page (e.g. CP1251 on Russian Windows)
    instead of UTF-8, producing garbled non-ASCII names.  Reverse this by
    re-encoding the garbled string as the system code page to recover the
    original UTF-8 bytes, then decoding those bytes as UTF-8.
    """
    try:
        import locale
        cp = locale.getpreferredencoding(False)
        if cp.lower() in ("utf-8", "utf8"):
            return name
        return name.encode(cp).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
        return name

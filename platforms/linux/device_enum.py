import os

from platforms.base.device_enum import DeviceEnumBase, DeviceInfo, DeviceType

_UID = str(os.getuid())


def _ensure_pulse_env() -> None:
    """Set PipeWire/PulseAudio socket vars if missing (SSH/screen launch)."""
    rt = f"/run/user/{_UID}"
    if not os.environ.get("XDG_RUNTIME_DIR"):
        os.environ["XDG_RUNTIME_DIR"] = rt
    if not os.environ.get("PULSE_SERVER"):
        sock = f"{rt}/pulse/native"
        if os.path.exists(sock):
            os.environ["PULSE_SERVER"] = f"unix:{sock}"


class DeviceEnum(DeviceEnumBase):

    def list_devices(self) -> list[DeviceInfo]:
        _ensure_pulse_env()
        import pyaudio
        pa = pyaudio.PyAudio()
        try:
            return _list_alsa_devices(pa)
        finally:
            pa.terminate()


def _list_alsa_devices(pa) -> list[DeviceInfo]:
    seen: set[str] = set()
    devices: list[DeviceInfo] = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] <= 0:
            continue
        name = info["name"]
        if name in seen:
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

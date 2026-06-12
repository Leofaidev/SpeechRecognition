from platforms.base.device_enum import DeviceEnumBase, DeviceInfo, DeviceType


class DeviceEnum(DeviceEnumBase):

    def list_devices(self) -> list[DeviceInfo]:
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

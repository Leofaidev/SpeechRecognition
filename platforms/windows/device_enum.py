from platforms.base.device_enum import DeviceEnumBase, DeviceInfo, DeviceType


class DeviceEnum(DeviceEnumBase):

    def list_devices(self) -> list[DeviceInfo]:
        import pyaudio  # imported lazily so the module loads without pyaudio at import time
        pa = pyaudio.PyAudio()
        devices: list[DeviceInfo] = []
        try:
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    devices.append(DeviceInfo(
                        id=i,
                        name=info["name"],
                        device_type=DeviceType.MICROPHONE,
                        channel_count=int(info["maxInputChannels"]),
                        sample_rate=float(info["defaultSampleRate"]),
                    ))
        finally:
            pa.terminate()
        return devices

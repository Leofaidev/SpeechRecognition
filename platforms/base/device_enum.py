import abc
from dataclasses import dataclass
from enum import Enum


class DeviceType(Enum):
    MICROPHONE = "microphone"
    WEBCAM = "webcam"


@dataclass
class DeviceInfo:
    id: int
    name: str
    device_type: DeviceType
    channel_count: int
    sample_rate: float


class DeviceEnumBase(abc.ABC):

    @abc.abstractmethod
    def list_devices(self) -> list[DeviceInfo]:
        """Return all available audio input devices."""

    def find_device(self, partial_name: str) -> DeviceInfo | None:
        """Case-insensitive partial-name match; returns the first match or None."""
        needle = partial_name.lower()
        for device in self.list_devices():
            if needle in device.name.lower():
                return device
        return None

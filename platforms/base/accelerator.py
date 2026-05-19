import abc
from dataclasses import dataclass


@dataclass
class AcceleratorInfo:
    name: str
    backend: str   # e.g. "cuda", "rocm", "openvino", "coreml", "cpu"
    device_index: int
    vram_bytes: int


class AcceleratorBase(abc.ABC):

    @abc.abstractmethod
    def list_devices(self) -> list[AcceleratorInfo]:
        """Return all available hardware accelerators."""

    @abc.abstractmethod
    def get_compute_device(self) -> str:
        """Return the device string to pass to ML frameworks (e.g. 'cuda:0', 'cpu')."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Return True if at least one non-CPU accelerator is available."""

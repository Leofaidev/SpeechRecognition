from platform.base.accelerator import AcceleratorBase, AcceleratorInfo

_PLATFORM = 'linux'

class Accelerator(AcceleratorBase):
    def list_devices(self) -> list[AcceleratorInfo]:
        raise NotImplementedError(
            f"Accelerator is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def get_compute_device(self) -> str:
        raise NotImplementedError(
            f"Accelerator is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def is_available(self) -> bool:
        raise NotImplementedError(
            f"Accelerator is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

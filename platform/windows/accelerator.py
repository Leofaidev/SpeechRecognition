from platform.base.accelerator import AcceleratorBase, AcceleratorInfo


class Accelerator(AcceleratorBase):

    def list_devices(self) -> list[AcceleratorInfo]:
        raise NotImplementedError("Accelerator.list_devices will be implemented in Phase 1-C")

    def get_compute_device(self) -> str:
        raise NotImplementedError("Accelerator.get_compute_device will be implemented in Phase 1-C")

    def is_available(self) -> bool:
        raise NotImplementedError("Accelerator.is_available will be implemented in Phase 1-C")

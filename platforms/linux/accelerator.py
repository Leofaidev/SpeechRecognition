from platforms.base.accelerator import AcceleratorBase, AcceleratorInfo


class Accelerator(AcceleratorBase):

    def list_devices(self) -> list[AcceleratorInfo]:
        try:
            import torch
            if not torch.cuda.is_available():
                return []
            devices = []
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                devices.append(AcceleratorInfo(
                    name=props.name,
                    backend="cuda",
                    device_index=i,
                    vram_bytes=props.total_memory,
                ))
            return devices
        except Exception:
            return []

    def get_compute_device(self) -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"

    def is_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

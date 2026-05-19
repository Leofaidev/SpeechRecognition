from platform.base.device_enum import DeviceEnumBase, DeviceInfo

_PLATFORM = 'macos'

class DeviceEnum(DeviceEnumBase):
    def list_devices(self) -> list[DeviceInfo]:
        raise NotImplementedError(
            f"DeviceEnum is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

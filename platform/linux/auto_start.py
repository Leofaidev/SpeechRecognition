from platform.base.auto_start import AutoStartBase

_PLATFORM = 'linux'

class AutoStart(AutoStartBase):
    def enable(self, app_path: str) -> None:
        raise NotImplementedError(
            f"AutoStart is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def disable(self) -> None:
        raise NotImplementedError(
            f"AutoStart is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def is_enabled(self) -> bool:
        raise NotImplementedError(
            f"AutoStart is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

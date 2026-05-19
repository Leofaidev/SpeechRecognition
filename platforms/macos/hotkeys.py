from platforms.base.hotkeys import HotkeysBase

_PLATFORM = 'macos'

class Hotkeys(HotkeysBase):
    def register(self, combination: str, callback) -> None:
        raise NotImplementedError(
            f"Hotkeys is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def unregister(self, combination: str) -> None:
        raise NotImplementedError(
            f"Hotkeys is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def unregister_all(self) -> None:
        raise NotImplementedError(
            f"Hotkeys is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def is_conflict(self, combination: str) -> bool:
        raise NotImplementedError(
            f"Hotkeys is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

from platform.base.tray import TrayBase

_PLATFORM = 'linux'

class Tray(TrayBase):
    def create(self, icon_path: str, menu_items: list[dict]) -> None:
        raise NotImplementedError(
            f"Tray is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def destroy(self) -> None:
        raise NotImplementedError(
            f"Tray is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def show_notification(self, title: str, message: str) -> None:
        raise NotImplementedError(
            f"Tray is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def set_menu_item_enabled(self, item_id: str, enabled: bool) -> None:
        raise NotImplementedError(
            f"Tray is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

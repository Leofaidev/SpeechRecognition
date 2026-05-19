from typing import Callable

from platforms.base.tray import TrayBase


class Tray(TrayBase):

    def create(self, icon_path: str, menu_items: list[dict]) -> None:
        raise NotImplementedError("Tray.create will be implemented in Phase 6-F")

    def destroy(self) -> None:
        raise NotImplementedError("Tray.destroy will be implemented in Phase 6-F")

    def show_notification(self, title: str, message: str) -> None:
        raise NotImplementedError("Tray.show_notification will be implemented in Phase 6-F")

    def set_menu_item_enabled(self, item_id: str, enabled: bool) -> None:
        raise NotImplementedError("Tray.set_menu_item_enabled will be implemented in Phase 6-F")

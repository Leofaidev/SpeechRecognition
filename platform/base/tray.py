import abc
from typing import Callable


class TrayBase(abc.ABC):

    @abc.abstractmethod
    def create(self, icon_path: str, menu_items: list[dict]) -> None:
        """Create the system tray icon with the given menu items."""

    @abc.abstractmethod
    def destroy(self) -> None:
        """Remove the tray icon."""

    @abc.abstractmethod
    def show_notification(self, title: str, message: str) -> None:
        """Display a balloon/toast notification from the tray icon."""

    @abc.abstractmethod
    def set_menu_item_enabled(self, item_id: str, enabled: bool) -> None:
        """Enable or disable a menu item by its id."""

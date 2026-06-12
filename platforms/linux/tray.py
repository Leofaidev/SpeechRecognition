"""Linux system tray via pystray (GTK/AppIndicator backend).

pystray is cross-platform; the TrayBase interface is fulfilled here for
completeness, but the GUI uses gui/tray.py (TrayIcon) directly.
"""
from __future__ import annotations

from typing import Callable

from platforms.base.tray import TrayBase


class Tray(TrayBase):

    def __init__(self) -> None:
        self._icon = None
        self._items: dict[str, object] = {}

    def create(self, icon_path: str, menu_items: list[dict]) -> None:
        try:
            import pystray
            from PIL import Image
            img = Image.open(icon_path).resize((64, 64)).convert("RGBA")
            menu = pystray.Menu(*[
                pystray.MenuItem(
                    item.get("label", ""),
                    item.get("callback"),
                    enabled=item.get("enabled", True),
                )
                for item in menu_items
            ])
            self._icon = pystray.Icon("wsp", img, menu=menu)
            import threading
            threading.Thread(target=self._icon.run, daemon=True).start()
        except Exception:
            pass

    def destroy(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass

    def show_notification(self, title: str, message: str) -> None:
        if self._icon is not None:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass

    def set_menu_item_enabled(self, item_id: str, enabled: bool) -> None:
        pass  # pystray menu items are rebuilt on each update

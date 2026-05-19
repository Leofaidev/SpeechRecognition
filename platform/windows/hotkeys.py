from typing import Callable

from platform.base.hotkeys import HotkeysBase

# Known Windows system shortcuts that should trigger a conflict warning (Spec 12.5.d)
_SYSTEM_SHORTCUTS = {
    "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z", "ctrl+y",
    "ctrl+a", "ctrl+s", "ctrl+p", "ctrl+f", "ctrl+w",
    "ctrl+alt+del", "alt+f4", "win+d", "win+l",
}


class Hotkeys(HotkeysBase):

    def register(self, combination: str, callback: Callable[[], None]) -> None:
        raise NotImplementedError("Hotkeys.register will be implemented in Phase 6-B")

    def unregister(self, combination: str) -> None:
        raise NotImplementedError("Hotkeys.unregister will be implemented in Phase 6-B")

    def unregister_all(self) -> None:
        raise NotImplementedError("Hotkeys.unregister_all will be implemented in Phase 6-B")

    def is_conflict(self, combination: str) -> bool:
        return combination.lower() in _SYSTEM_SHORTCUTS

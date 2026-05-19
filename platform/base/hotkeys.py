import abc
from typing import Callable


class HotkeysBase(abc.ABC):

    @abc.abstractmethod
    def register(self, combination: str, callback: Callable[[], None]) -> None:
        """Register a global hotkey combination (e.g. 'ctrl+shift+r')."""

    @abc.abstractmethod
    def unregister(self, combination: str) -> None:
        """Unregister a previously registered hotkey combination."""

    @abc.abstractmethod
    def unregister_all(self) -> None:
        """Unregister all hotkeys registered through this instance."""

    @abc.abstractmethod
    def is_conflict(self, combination: str) -> bool:
        """Return True if combination conflicts with a known system shortcut."""

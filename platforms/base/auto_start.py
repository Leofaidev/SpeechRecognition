import abc


class AutoStartBase(abc.ABC):

    @abc.abstractmethod
    def enable(self, app_path: str) -> None:
        """Register the application to launch on user login."""

    @abc.abstractmethod
    def disable(self) -> None:
        """Remove the auto-start registration."""

    @abc.abstractmethod
    def is_enabled(self) -> bool:
        """Return True if auto-start is currently registered."""

import abc


class DataDirsBase(abc.ABC):
    APP_NAME = "SpeechRecognitionProgram"

    @abc.abstractmethod
    def get_app_dir(self) -> str:
        """Return the root application data directory path."""

    @abc.abstractmethod
    def ensure_app_dir(self) -> str:
        """Create the app directory if it does not exist and return its path."""

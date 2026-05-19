from platform.base.auto_start import AutoStartBase

_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "SpeechRecognitionProgram"


class AutoStart(AutoStartBase):

    def enable(self, app_path: str) -> None:
        raise NotImplementedError("AutoStart.enable will be implemented in Phase 6-F")

    def disable(self) -> None:
        raise NotImplementedError("AutoStart.disable will be implemented in Phase 6-F")

    def is_enabled(self) -> bool:
        raise NotImplementedError("AutoStart.is_enabled will be implemented in Phase 6-F")

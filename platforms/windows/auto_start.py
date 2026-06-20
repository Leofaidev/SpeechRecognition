import sys
import winreg
from platforms.base.auto_start import AutoStartBase

_REG_KEY    = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "SpeechRecognitionProgram"


class AutoStart(AutoStartBase):

    def enable(self, app_path: str) -> None:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY,
                            access=winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, _VALUE_NAME, 0, winreg.REG_SZ,
                              f'"{app_path}"')

    def disable(self) -> None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY,
                                access=winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, _VALUE_NAME)
        except FileNotFoundError:
            pass

    def is_enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY) as k:
                winreg.QueryValueEx(k, _VALUE_NAME)
                return True
        except FileNotFoundError:
            return False

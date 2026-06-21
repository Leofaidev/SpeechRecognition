import sys
import winreg
from platforms.base.auto_start import AutoStartBase

_REG_KEY    = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "WSP"


class AutoStart(AutoStartBase):

    def enable(self, app_path: str) -> None:
        cmd = _build_launch_command(app_path)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY,
                            access=winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, _VALUE_NAME, 0, winreg.REG_SZ, cmd)

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


def _build_launch_command(app_path: str) -> str:
    """Return the registry command string that will launch the app at logon.

    Installed (PyInstaller): sys.frozen is True and app_path is the bundled
    exe — write it directly.

    Source/dev: app_path is pythonw.exe; reconstruct the full '-m gui.app'
    invocation with the src directory injected into sys.path so the import
    works regardless of the CWD that Windows assigns at logon.
    """
    if getattr(sys, "frozen", False):
        return f'"{app_path}"'

    # Derive the src/ directory from the running entry-point file.
    # sys.argv[0] when running 'pythonw -m gui.app' from src/ is
    # '<src>/gui/app.py', so parent.parent == src/.
    import pathlib
    try:
        src_dir = str(pathlib.Path(sys.argv[0]).resolve().parent.parent)
    except Exception:
        src_dir = ""

    if src_dir:
        escaped = src_dir.replace("'", "\\'")
        snippet = (
            f"import sys; sys.path.insert(0, r'{escaped}'); "
            f"import runpy; runpy.run_module('gui.app', run_name='__main__')"
        )
        return f'"{app_path}" -c "{snippet}"'

    # Fallback: best-effort (may fail if CWD is not src/ at logon)
    return f'"{app_path}" -m gui.app'

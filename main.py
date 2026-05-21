"""Entry point: dispatch to CLI (any arguments) or GUI (no arguments)."""
from __future__ import annotations

import sys
from pathlib import Path

# When running from source (not bundled by PyInstaller), add src/ to sys.path
# so that ``from cli.parser import …`` and ``from gui.app import …`` resolve.
if not getattr(sys, "frozen", False):
    _src = Path(__file__).parent / "src"
    if _src.is_dir() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))


def _ensure_no_console() -> None:
    """GUI mode: re-launch with pythonw.exe so no console window ever appears.

    python.exe allocates a console before any Python code runs, so FreeConsole()
    always flashes.  Re-launching as pythonw.exe avoids the window entirely.
    If pythonw.exe is not found (unusual), fall back to hiding the window.
    """
    if sys.platform != "win32":
        return
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        return  # already running without a console

    pythonw = exe.parent / "pythonw.exe"
    if pythonw.exists():
        import subprocess
        # Re-launch this exact script with pythonw.exe, then exit immediately.
        subprocess.Popen(
            [str(pythonw), str(Path(__file__).resolve())] + sys.argv[1:],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        sys.exit(0)
    else:
        # pythonw.exe not available — at least hide the console window
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass


def _close_existing_instance(pid_file: Path) -> None:
    """Kill any previous GUI instance recorded in *pid_file*."""
    if not pid_file.exists():
        return
    try:
        old_pid = int(pid_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return
    if old_pid == 0:
        return
    import subprocess, time
    subprocess.run(
        ["taskkill", "/PID", str(old_pid), "/T", "/F"],
        capture_output=True,
    )
    time.sleep(0.8)  # let the OS reclaim resources before we start


def _write_pid(pid_file: Path) -> None:
    import os
    try:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        pass


def main() -> None:
    if len(sys.argv) > 1:
        from cli.parser import main as cli_main
        sys.exit(cli_main())
    else:
        _ensure_no_console()
        from config.store import ConfigStore
        from gui.app import run
        from platforms.windows.data_dirs import DataDirs
        from pathlib import Path as _Path
        app_dir = DataDirs().ensure_app_dir()
        pid_file = _Path(app_dir) / "app.pid"
        _close_existing_instance(pid_file)
        _write_pid(pid_file)
        config_path = _Path(app_dir) / "config.json"
        try:
            run(ConfigStore(config_path))
        finally:
            try:
                pid_file.write_text("0", encoding="utf-8")
            except OSError:
                pass


if __name__ == "__main__":
    main()

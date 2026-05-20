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


def _detach_console() -> None:
    """Hide the inherited console window when launching in GUI mode on Windows."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.FreeConsole()


def main() -> None:
    if len(sys.argv) > 1:
        from cli.parser import main as cli_main
        sys.exit(cli_main())
    else:
        _detach_console()
        from config.store import ConfigStore
        from gui.app import run
        run(ConfigStore())


if __name__ == "__main__":
    main()

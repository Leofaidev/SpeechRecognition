# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Speech Recognition Program (wsp.exe).
# Produces a one-directory bundle under dist/wsp/.
#
# Prerequisites (run once before pyinstaller wsp.spec):
#   pip install -r requirements.txt
#
# Build:
#   pyinstaller wsp.spec
#
# Model files (*.bin, *.safetensors, etc.) are intentionally excluded.
# They are downloaded during Inno Setup installation into {app}\models\.

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

# ---------------------------------------------------------------------------
# Data files
# ---------------------------------------------------------------------------

datas = []

# CustomTkinter theme files (required at runtime)
datas += collect_data_files("customtkinter")

# faster-whisper tokenizer configs
datas += collect_data_files("faster_whisper")

# Our own directories
datas += [
    ("languages", "languages"),
    ("assets", "assets"),
    ("platforms", "platforms"),
]

# ---------------------------------------------------------------------------
# Native binaries (DLLs)
# ---------------------------------------------------------------------------

binaries = []

# ctranslate2 native DLLs (CPU + CUDA inference backend)
binaries += collect_dynamic_libs("ctranslate2")

# ---------------------------------------------------------------------------
# Hidden imports — modules not discovered by static analysis
# ---------------------------------------------------------------------------

# Platform modules loaded conditionally based on sys.platform
_platform_mods = [
    "windows", "linux", "macos",
]
_platform_subs = [
    "accelerator", "auto_start", "data_dirs", "device_enum",
    "hotkeys", "installer", "tray",
]
hiddenimports = [
    f"platforms.{p}.{s}"
    for p in _platform_mods
    for s in _platform_subs
] + [
    f"platforms.{p}" for p in _platform_mods
] + [
    "platforms.base",
    "platforms.base.accelerator",
    "platforms.base.auto_start",
    "platforms.base.data_dirs",
    "platforms.base.device_enum",
    "platforms.base.hotkeys",
    "platforms.base.installer",
    "platforms.base.tray",
]

# pyannote submodules — some are imported dynamically by the pipeline
hiddenimports += collect_submodules("pyannote.audio")
hiddenimports += collect_submodules("pyannote.core")
hiddenimports += collect_submodules("pyannote.pipeline")

# PIL backend for Tkinter (needed by CustomTkinter)
hiddenimports += ["PIL._tkinter_finder"]

# pyperclip backends
hiddenimports += ["pyperclip.handlers"]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

a = Analysis(
    ["main.py"],
    pathex=["src"],             # resolves cli.*, gui.*, config.* etc.
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["runtime_hooks/hook_app_dirs.py"],
    excludes=[
        # Test packages — not needed in the bundle
        "pytest",
        "pytest_mock",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

# ---------------------------------------------------------------------------
# Executable
# ---------------------------------------------------------------------------

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,      # binaries go into COLLECT (one-dir mode)
    name="wsp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,               # console=True so CLI stdout/stderr are visible
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/WSP.ico",
)

# ---------------------------------------------------------------------------
# One-directory collection (dist/wsp/)
# ---------------------------------------------------------------------------

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="wsp",
)

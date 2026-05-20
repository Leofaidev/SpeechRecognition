# Build Instructions

Step-by-step guide for producing the distributable Windows installer from source.

**Spec reference:** Sections 15.1.h, 16.1, 16.4.c

---

## Prerequisites

Install the following tools before building. All must be on your `PATH`.

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.14+ | Must match the version used for development |
| PyInstaller | 6.20.0 | Installed via `pip install -r requirements.txt` |
| Inno Setup | 6.2+ | Download from [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php) — not a pip package |
| FFmpeg | Latest stable | Required at runtime; must be on `PATH` |
| CUDA Toolkit | 12.6+ | Only needed if building the CUDA-enabled package |

---

## Step 1 — Prepare the environment

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Verify all imports succeed:

```bat
python -c "import faster_whisper, pyannote.audio, customtkinter, pyaudio, cv2, keyboard"
```

---

## Step 2 — Run the test suite

All unit tests must pass before building.

```bat
pytest tests/unit/ -q
```

---

## Step 3 — Bundle with PyInstaller

The `wsp.spec` file in the repository root controls the bundle. Run from the repo root:

```bat
pyinstaller wsp.spec
```

This produces `dist/wsp/` containing the bundled application. The spec:

- Entry point: `main.py` (dispatches to CLI or GUI based on `sys.argv`)
- Includes all Python packages from `requirements.txt`
- Includes `languages/`, `assets/`, and `platforms/` directories
- Excludes Whisper and pyannote model files (downloaded at install time into `{app}\models\`)
- Sets the executable name to `wsp.exe`
- One-directory mode (not one-file) for faster startup and easier model placement
- Runtime hook `runtime_hooks/hook_app_dirs.py` sets `HF_HOME={app}\models` when frozen

**Notes on the console flag:**
`wsp.exe` is built with `console=True` so that CLI output (`--input`, `--backup`, etc.) is
visible in a terminal. When launched via the desktop shortcut (no arguments), `main.py`
calls `FreeConsole()` immediately to suppress the console window before opening the GUI.

---

## Step 4 — Build the Inno Setup installer

The script `installer/wsp_setup.iss` implements:

| Feature | Details |
|---------|---------|
| Default path | `%LOCALAPPDATA%\SpeechRecognitionProgram` |
| Custom path | User-selectable; disk-space check enforced (minimum 10 GB) |
| VLC check | Detects via registry; downloads VLC 3.0.21 Win64 if absent |
| HuggingFace licence page | Custom wizard page with Accept / Decline radio buttons |
| Whisper model selection | Custom page: Tiny / Base / Small / Medium ✓ / Large v3 |
| Model download | Per-file progress via `TDownloadWizardPage`; retry on failure; partial files deleted |
| Config initialisation | Writes `{app}\config.json` with `whisper_model`, `whisper_model_path`, `licence_accepted` |
| Shortcuts | Desktop shortcut (optional task) + Start Menu entry |
| Uninstaller | Standard Inno Setup uninstaller removes all app files |

Compile the installer (adjust path if Inno Setup is installed elsewhere):

```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\wsp_setup.iss
```

The compiled installer is written to `installer\Output\wsp_setup.exe`.

**Model file layout after installation:**

```
{app}\
  wsp.exe
  ...                            ← PyInstaller bundle
  models\
    faster-whisper-medium\       ← (or tiny / base / small / large-v3)
      model.bin
      config.json
      vocabulary.json
      tokenizer.json
      preprocessor_config.json
  config.json                    ← written by installer; read by ConfigStore on first launch
```

**pyannote / diarization models:**
These require a HuggingFace account and model-gating acceptance.
The runtime hook redirects `HF_HOME` to `{app}\models`, so models download there
automatically on first use (when `licence_accepted = true` in config).

---

## Step 5 — Test the installer

Run the installer on a **clean Windows VM** (no Python, no VLC pre-installed) and verify
CHK-123 through CHK-135 in `docs/WorkPlan.md`. Key checks:

1. Disk space check fires if < 10 GB free on the selected drive.
2. VLC is downloaded and installed if absent; existing VLC is reused if present.
3. HuggingFace licence page is displayed; declining disables speaker identification on first launch.
4. Whisper model selection works; only the selected model's five files are downloaded.
5. Simulated download failure (disconnect mid-download): error + retry offered; no partial files remain.
6. Application launches after installation; all nine GUI panels open.
7. Processing a short WAV file produces output.

---

## Step 6 — Create the GitHub Release

1. Tag the commit: `git tag v1.0.0 && git push origin v1.0.0`
2. Create the release on GitHub:
   - Attach `installer\Output\wsp_setup.exe`
   - Attach the approved wireframe PDF
   - Paste the release notes (see `docs/WorkPlan.md` T-125)

Release notes must include:
- Version number and release date
- Feature list
- Known issues (Russian/Chinese translation quality pending native-speaker review)
- Full list of bundled libraries and their licences

---

## Updating `requirements.txt`

After any `pip install` or version change, regenerate the pinned requirements file:

```bat
pip freeze > requirements.txt
```

Verify no library used in source is absent from `requirements.txt` before committing (CHK-05, CHK-157).

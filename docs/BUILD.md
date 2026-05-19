# Build Instructions

Step-by-step guide for producing the distributable Windows installer from source.

**Spec reference:** Sections 15.1.h, 16.1, 16.4.c

---

## Prerequisites

Install the following tools before building. All must be on your `PATH`.

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.14+ | Must match the version used for development |
| PyInstaller | See `requirements.txt` | Installed via pip |
| Inno Setup | 6.x | Download from [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php) — not a pip package |
| FFmpeg | Latest stable | Required at runtime; bundle into the installer |
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

A `wsp.spec` file in the repository root controls the bundle. Run:

```bat
pyinstaller wsp.spec
```

This produces a `dist/wsp/` folder containing the bundled application. The spec file:

- Includes all Python packages from `requirements.txt`
- Includes `languages/`, `assets/sounds/`, and `platform/` directories
- Excludes Whisper and pyannote.audio model files (downloaded during installation)
- Sets the executable name to `wsp.exe`
- Enables one-directory mode (not one-file) for faster startup

> `wsp.spec` will be committed to the repository at the start of Phase 7.

---

## Step 4 — Build the Inno Setup installer

The Inno Setup script `installer/wsp_setup.iss` defines:

- Default installation path: `%LOCALAPPDATA%\SpeechRecognitionProgram`
- Custom path selection dialog
- Disk space check (minimum 10 GB)
- VLC detection and conditional download
- HuggingFace licence acceptance page
- Whisper model selection screen (tiny / base / small / medium ✓ / large)
- Model download with per-file progress and retry on failure
- Desktop shortcut and Start Menu entry

Compile the installer:

```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\wsp_setup.iss
```

The compiled installer is written to `installer\Output\wsp_setup.exe`.

> `installer/wsp_setup.iss` will be committed to the repository at the start of Phase 7.

---

## Step 5 — Test the installer

Run the installer on a **clean Windows VM** (no Python, no VLC pre-installed) and verify:

1. Disk space check fires if < 10 GB free.
2. VLC is downloaded and installed if absent; existing VLC is reused if present.
3. HuggingFace licence is displayed; declining disables diarization on first launch.
4. Whisper model selection works; only the selected model is downloaded.
5. Model download failure shows an error and retry button; no partial files remain.
6. Application launches successfully after installation.
7. All nine GUI panels open.
8. Processing a short WAV file produces output.

See CHK-123 through CHK-135 in `docs/WorkPlan.md` for the full acceptance checklist.

---

## Step 6 — Create the GitHub Release

1. Tag the commit: `git tag v1.0.0 && git push origin v1.0.0`
2. Create the release on GitHub:
   - Attach `installer\Output\wsp_setup.exe`
   - Attach the approved wireframe PDF
   - Paste the release notes (version, date, features, bug fixes, known issues)

Release notes must include:
- Version number and release date
- New features
- Bug fixes
- Known issues (including Russian/Chinese translation quality pending native-speaker review)
- List of all bundled libraries and their licences

---

## Updating `requirements.txt`

After any `pip install` or version change, regenerate the pinned requirements file:

```bat
pip freeze > requirements.txt
```

Verify no library used in source is absent from `requirements.txt` before committing (CHK-05, CHK-157).

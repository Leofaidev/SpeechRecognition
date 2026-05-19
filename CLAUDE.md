# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Locally executed, GPU-accelerated speech recognition application written in Python. Converts spoken audio into text, identifies individual speakers, optionally translates the result, and delivers output in multiple configurable formats.

- **Spec:** `docs/Specification.md` (v1.0 Final)
- **Work plan:** `docs/WorkPlan.md` (Phases 0–9, 133 tasks, 176 checks)
- **Target OS:** Windows 10/11 64-bit (future: Ubuntu, Debian, macOS via stubs)
- **Primary GPU:** NVIDIA RTX 3060 Ti via CUDA; must also run on CPU

## Getting Started

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install all dependencies (pinned versions)
pip install -r requirements.txt

# Verify CUDA availability
python -c "import faster_whisper; print('ok')"
```

Build and installer instructions will live in `BUILD.md` once the installer is implemented (Phase 7).

## Architecture

### Planned module structure (`src/`)

| Module | Responsibility |
|--------|----------------|
| `audio.ingest` | Load MP3/WAV/MP4/AVI → normalised mono 16 kHz WAV buffer via FFmpeg |
| `audio.device` | Enumerate microphone/webcam devices via pyaudio |
| `audio.capture` | Record from a selected device; stream splitting at 5-hour boundary |
| `diarization.engine` | Speaker diarization via pyannote.audio; HuggingFace licence check |
| `transcription.engine` | Speech-to-text via faster-whisper; bad-audio detection (`no_speech_prob > 0.6`) |
| `dictionary.store/matcher/importer/exporter` | Substitution dictionary (case-insensitive, whole-word, fnmatch wildcards) |
| `translation.opus_mt` / `translation.google` | Local (Helsinki-NLP OPUS-MT) and online (Google Translate) translation |
| `translation.engine` | Dispatcher; applies translation after substitution |
| `output.*_writer` | Writers for TXT, DOCX, SRT, JSON, clipboard; `_WSP` file naming |
| `library.storage/profile_creator/retrainer/groups/importer/exporter` | Voice profile library: speaker subfolders, `speaker.json`, embeddings, retraining |
| `session.manager` / `session.history` | Session lifecycle, retroactive relabelling, session JSON persistence |
| `config.store` | JSON config file; all persistent settings with defaults |
| `backup.manager` / `backup.restorer` | ZIP backup/restore of all user data |
| `cli.parser` | argparse CLI front-end (no GUI); all output always in English |
| `platform/windows/` | Windows-specific: data dirs (`%LOCALAPPDATA%`), auto-start (HKCU), tray, hotkeys, device enum |
| `platform/linux/` `platform/macos/` | Stubs raising `NotImplementedError` |

### Processing pipeline (fixed order)
1. Speaker diarization (pyannote.audio)
2. Speech-to-text per segment (faster-whisper)
3. Language detection
4. Substitution dictionary
5. Translation (if enabled)
6. Output to active destinations

### GUI
Built with **CustomTkinter**. Nine panels: Settings, Voice Profile Management, Substitution Dictionary, Batch Queue, Output Content Configuration, Hotkey Configuration, Speaker Labelling Prompt, Session History, Backup and Restore.

### Output file naming
`<input_name>_WSP.<ext>` — collisions resolved with numeric suffix (`_2`, `_3`, …); stream splits use `_part1`, `_part2`, …

## Key Constraints

- All core processing (speech recognition, speaker ID) must run **locally**. Translation is the only feature that may optionally use an external service.
- All libraries must be **free and open-source** and listed in `requirements.txt` with pinned versions.
- pyannote.audio requires **HuggingFace licence acceptance**; if absent, all diarization features are disabled and speakers are labelled Unknown.
- Platform-specific code must be **isolated in `platform/`** modules to support future ports.
- CLI mode: no GUI, all output in English, exit code 0 on success.

## Preferred Libraries

| Library | Role |
|---------|------|
| faster-whisper | Speech-to-text, language detection (CUDA) |
| pyannote.audio | Speaker diarization |
| FFmpeg | Audio extraction from MP4/AVI |
| CustomTkinter | GUI |
| pyaudio | Microphone/webcam audio capture |
| OpenCV | Webcam video stream |
| keyboard | Global hotkeys (Windows) |
| Helsinki-NLP OPUS-MT | Local translation |
| python-vlc | Audio/video playback (requires VLC installed) |
| PyInstaller | App bundling |
| Inno Setup | Windows installer |

## Development Phases

| Phase | Focus |
|-------|-------|
| 0 | Project setup, stubs, wireframes, test fixtures |
| 1-A–F | Core audio pipeline (ingestion, diarization, transcription, dictionary, translation, output) |
| 2 | Voice profile library |
| 3 | Session management and history |
| 4 | Configuration, settings, backup |
| 5 | CLI front-end |
| 6 | GUI (all panels, tray, hotkeys, Short Session two-field form) |
| 7 | Installer (PyInstaller + Inno Setup) |
| 8 | Integration, performance, regression testing |
| 9 | Documentation and GitHub Release v1.0 |

Current status: **Phase 0** — no source code yet.

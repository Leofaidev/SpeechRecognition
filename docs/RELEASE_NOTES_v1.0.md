# Release Notes — v1.0.0

**Release date:** 2026-05-21

---

## Overview

First stable release of Speech Recognition Program. The application converts spoken audio into text, identifies individual speakers, optionally translates the result, and delivers output in multiple configurable formats — all running locally on Windows with GPU acceleration.

---

## Features

### Audio Input
- File processing: MP3, WAV, MP4, AVI
- Microphone / webcam capture with configurable device selection
- Regular session and Short Session (two-field transcription + translation form) modes
- Automatic stream splitting at the 5-hour boundary; speaker numbering is continuous across parts

### Speech Recognition
- Faster-whisper speech-to-text engine
- Available models: Tiny, Base, Small, Medium (recommended), Large v3
- CUDA-accelerated on NVIDIA GPUs; CPU fallback supported
- Automatic language detection per file

### Speaker Diarization
- pyannote.audio — up to 10 simultaneous speakers
- Requires HuggingFace model licence acceptance; gracefully disabled if absent
- Voice profile library: extract 10-second samples, store named speaker profiles
- Speaker group management for context-specific identification
- Retraining triggered automatically when the Whisper model changes

### Translation
- Local (offline): Helsinki-NLP OPUS-MT
- Online: Google Translate
- Per-segment translated text stored alongside source text in output

### Output
- Formats: plain text (TXT), DOCX, SRT subtitles, JSON, clipboard
- Configurable output fields: timestamp, speaker, language, confidence, text, translation
- Output file naming: `<input>_WSP.<ext>`; numeric suffix on collision; `_part1`/`_part2` for stream splits

### GUI (CustomTkinter)
- Nine panels: Settings, Voice Profile Management, Substitution Dictionary, Batch Queue, Output Configuration, Hotkey Configuration, Speaker Labelling, Session History, Backup and Restore
- System tray icon with notification and mode indicator
- Configurable global hotkeys (system-wide)
- Playback of processed audio via python-vlc

### CLI
- Full CLI mode — no GUI launched
- Batch file processing, profile management, dictionary import/export, backup/restore, session history
- All output in English regardless of configured UI language
- Exit codes: 0 success, 1 bad argument, 2 missing input, 3 file not found, 4 output not writable, 5 session not found, 10 translation error, 20 library error
- See `docs/CLI.md` for the complete parameter reference

### Installer
- Inno Setup wizard for Windows 10/11
- Selectable install path; disk space check (minimum 10 GB)
- VLC detection and automatic download if absent
- HuggingFace licence acceptance page
- Whisper model selection with per-file download progress and retry on failure
- Writes `config.json` on first launch with selected model and licence state

### Localisation
- 7 UI languages: English, German (Deutsch), Spanish (Español), Finnish (Suomi), Russian (Русский), Simplified Chinese (简体中文), Traditional Chinese (繁體中文)
- Automatic fallback to backup language file if the active file is corrupt

---

## Known Issues

| Issue | Status |
|-------|--------|
| Russian UI translation quality | Automated translation — pending native-speaker review |
| Chinese (Simplified and Traditional) UI translation quality | Automated translation — pending native-speaker review |
| CHK-138: Microphone Regular mode end-to-end | Manual test not yet completed |
| CHK-139: Short Session mode | Manual test not yet completed |
| CHK-151: GUI responsiveness during background processing | Manual test not yet completed |
| CHK-04: Wireframe approval | Written approval comment on GitHub issue pending |
| T-118/T-119: Clean Windows 10/11 VM installer test | Not yet run |

---

## Bundled Libraries and Licences

| Library | Version | Licence |
|---------|---------|---------|
| faster-whisper | 1.2.1 | MIT |
| pyannote.audio | 4.0.4 | MIT |
| pyannote.core | 6.0.1 | MIT |
| customtkinter | 5.2.2 | MIT |
| PyAudio | 0.2.14 | MIT |
| opencv-python | 4.13.0.92 | Apache 2.0 |
| keyboard | 0.13.5 | MIT |
| transformers | 5.8.1 | Apache 2.0 |
| sentencepiece | 0.2.1 | Apache 2.0 |
| sacremoses | 0.1.1 | MIT |
| python-vlc | 3.0.21203 | LGPL 2.1 |
| python-docx | 1.2.0 | MIT |
| pyperclip | 1.11.0 | BSD 3-Clause |
| pystray | 0.19.5 | LGPL 3.0 |
| torch | 2.12.0+cu126 | BSD 3-Clause |
| torchaudio | 2.11.0 | BSD 3-Clause |
| numpy | 2.4.6 | BSD 3-Clause |
| scipy | 1.17.1 | BSD 3-Clause |
| huggingface_hub | 1.15.0 | Apache 2.0 |
| PyInstaller | 6.20.0 | GPL + bootloader exception |
| Inno Setup | 6.2+ | Inno Setup Licence |

Full pinned version list: see `requirements.txt`.

---

## Upgrade Path

No upgrade path from a prior version (this is the initial release). To update, uninstall via the Windows Control Panel or Settings, then install the new version. User data (voice profiles, dictionary, session history, config) is stored in `%LOCALAPPDATA%\SpeechRecognitionProgram` and is not removed by the uninstaller.

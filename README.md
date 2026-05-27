# Speech Recognition Program

A locally executed, GPU-accelerated speech recognition desktop application for Windows. Converts spoken audio into text, identifies individual speakers, optionally translates the result, and delivers output in multiple configurable formats.

**Version 1.0** — released 2026-05-21

[Deutsch](README.de.md) | [Español](README.es.md) | [Suomi](README.fi.md) | [Русский](README.ru.md) | [简体中文](README.zh_CN.md) | [繁體中文](README.zh_TW.md)

---

## Features

- Speech-to-text via faster-whisper (CUDA-accelerated; CPU fallback supported)
- Speaker diarization via pyannote.audio — up to 10 simultaneous speakers
- Local translation (Helsinki-NLP OPUS-MT, offline) or online (Google Translate)
- Output formats: plain text, DOCX, SRT subtitles, JSON, clipboard
- Batch file processing with FIFO queue
- Voice profile library: store and identify named speakers across sessions
- Speaker group management for context-specific identification
- Configurable global hotkeys (system-wide, even when minimised)
- Regular and Short Session recording modes
- GUI (CustomTkinter) and full CLI modes
- System tray integration with notifications
- Session history with retroactive output regeneration
- Backup and restore of all user data

---

## System Requirements

| Requirement | Details |
|-------------|---------|
| OS | Windows 10 or 11, 64-bit |
| GPU | NVIDIA GPU with CUDA recommended (RTX 3060 Ti or better); CPU fallback supported |
| RAM | 4 GB minimum; 8 GB recommended for 30-minute+ files |
| Disk | 10 GB free (covers all Whisper model sizes and OPUS-MT language pairs) |
| VLC | Required for audio playback — installer downloads VLC automatically if absent |
| FFmpeg | Required for MP4/AVI extraction — must be on PATH when running from source |

---

## Quick Start — Installer

1. Download `wsp_setup.exe` from the [latest GitHub Release](../../releases/latest).
2. Run the installer and follow the wizard:
   - Select a Whisper model (Medium is recommended).
   - Accept the HuggingFace pyannote licence if you want speaker identification.
3. Launch **Speech Recognition Program** from the desktop shortcut or Start Menu.
4. Select an input device or drop an audio file into the batch queue and press **Start**.

---

## Quick Start — From Source

```bat
git clone https://github.com/Leofaidev/SpeechRecognition.git
cd SpeechRecognition
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

> **Note:** PyAudio requires Microsoft C++ Build Tools and PortAudio via vcpkg before `pip install`.
> See the comments at the top of `requirements.txt` for step-by-step instructions.
> FFmpeg must be installed system-wide and on PATH.

---

## Command-Line Usage

```bat
wsp.exe --input interview.mp3 --output-format txt json
wsp.exe --input a.mp3 b.wav --output-folder C:\Output --speaker-group "Interviewers"
wsp.exe --backup C:\Backups\wsp_backup.zip
wsp.exe --help
```

See [docs/CLI.md](docs/CLI.md) for the full parameter reference and exit codes.

---

## UI Languages

English, German, Spanish, Finnish, Russian, Simplified Chinese, Traditional Chinese.

> Russian and Chinese translations are automated. Native-speaker review is pending.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/Specification.md](docs/Specification.md) | Full technical specification (v1.0) |
| [docs/WorkPlan.md](docs/WorkPlan.md) | Phase-by-phase work plan (Phases 0–9) |
| [docs/CLI.md](docs/CLI.md) | Command-line parameter reference |
| [docs/BUILD.md](docs/BUILD.md) | Installer build instructions (from source) |
| [docs/SPEAKER_JSON_SCHEMA.md](docs/SPEAKER_JSON_SCHEMA.md) | Voice profile `speaker.json` format |
| [docs/SESSION_JSON_SCHEMA.md](docs/SESSION_JSON_SCHEMA.md) | Session history JSON format |
| [docs/RELEASE_NOTES_v1.0.md](docs/RELEASE_NOTES_v1.0.md) | v1.0 release notes |

---

## Libraries

All libraries are free and open-source. See `requirements.txt` for pinned versions.

| Library | Role | Licence |
|---------|------|---------|
| faster-whisper | Speech-to-text and language detection | MIT |
| pyannote.audio | Speaker diarization (HuggingFace licence required) | MIT |
| CustomTkinter | Graphical user interface | MIT |
| pyaudio | Microphone and webcam audio capture | MIT |
| OpenCV | Webcam video stream access | Apache 2.0 |
| keyboard | Global hotkeys | MIT |
| transformers + sentencepiece | Helsinki-NLP OPUS-MT local translation | Apache 2.0 |
| python-vlc | Audio/video playback | LGPL 2.1 |
| python-docx | DOCX output | MIT |
| PyInstaller | Application bundling | GPL + bootloader exception |
| Inno Setup | Windows installer (separate tool) | Inno Setup Licence |
| PyTorch | Deep learning runtime | BSD 3-Clause |

> **HuggingFace licence:** pyannote.audio requires accepting the HuggingFace model licence.
> If not accepted, speaker identification is disabled and all speakers are labelled Unknown.

---

## Contributing / Issues

This is a private repository. To report a bug or request a feature, open an issue on GitHub.

# Speech Recognition Program

A locally executed, GPU-accelerated speech recognition application that converts spoken audio into text, identifies individual speakers, optionally translates the result, and delivers output in multiple configurable formats.

## Features

- Speech-to-text via faster-whisper (CUDA-accelerated, RTX 3060 Ti or CPU fallback)
- Speaker diarization via pyannote.audio (up to 10 simultaneous speakers)
- Translation: local (Helsinki-NLP OPUS-MT) or online (Google Translate)
- Output formats: plain text, DOCX, SRT subtitles, JSON, clipboard
- Batch file processing with FIFO queue
- Voice profile library with speaker identification and group management
- Configurable global hotkeys (system-wide, even when minimised)
- GUI (CustomTkinter) and full CLI modes
- Regular and Short Session recording modes

## System Requirements

- Windows 10 or 11 (64-bit)
- Python 3.14+
- NVIDIA GPU with CUDA support recommended (RTX 3060 Ti or better); CPU fallback supported
- VLC media player installed system-wide (required for audio playback via python-vlc)
- FFmpeg on PATH (required for MP4/AVI audio extraction)
- 10 GB free disk space (covers all Whisper model sizes and OPUS-MT language pairs)

## Quick Start

```bat
git clone https://github.com/Leofaidev/SpeechRecognition.git
cd SpeechRecognition
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Command-Line Usage

```
wsp.exe --input audio.mp3 --output-format txt json
wsp.exe --help
```

See [docs/CLI.md](docs/CLI.md) for the full parameter reference.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/Specification.md](docs/Specification.md) | Full technical specification (v1.0) |
| [docs/WorkPlan.md](docs/WorkPlan.md) | Phase-by-phase work plan (Phases 0–9) |
| [docs/CLI.md](docs/CLI.md) | Command-line parameter reference |
| [docs/BUILD.md](docs/BUILD.md) | Installer build instructions |
| [docs/SPEAKER_JSON_SCHEMA.md](docs/SPEAKER_JSON_SCHEMA.md) | speaker.json file format |
| [docs/SESSION_JSON_SCHEMA.md](docs/SESSION_JSON_SCHEMA.md) | Session history JSON format |

## Libraries

All libraries are free and open-source. See `requirements.txt` for pinned versions.

| Library | Role |
|---------|------|
| faster-whisper | Speech-to-text and language detection |
| pyannote.audio | Speaker diarization (HuggingFace licence required) |
| CustomTkinter | Graphical user interface |
| pyaudio | Microphone and webcam audio capture |
| OpenCV | Webcam video stream access |
| keyboard | Global hotkeys |
| Helsinki-NLP OPUS-MT (transformers) | Local translation |
| python-vlc | Audio/video playback |
| PyInstaller | Application bundling |
| Inno Setup | Windows installer (separate tool, not a Python package) |

> **Note — HuggingFace licence:** pyannote.audio requires accepting the HuggingFace model licence.
> If the licence is not accepted, all speaker identification features are disabled and speakers are labelled Unknown.

## Development Status

Currently at **Phase 0** (project setup). See [docs/WorkPlan.md](docs/WorkPlan.md) for the full roadmap.

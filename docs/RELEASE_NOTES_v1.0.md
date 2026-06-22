# Release Notes — v1.0.0

**Release date:** 2026-06-20

---

## Overview

First stable release of Speech Recognition Program. The application converts spoken audio into text, identifies individual speakers, optionally translates the result, and delivers output in multiple configurable formats — all running locally on Windows with GPU acceleration.

---

## ⚠️ Important: Recognition Models Are Not Included

The installer **does not bundle** speech recognition or speaker diarization models.
On the **first launch**, the application downloads the selected Whisper model from the internet:

| Model | Approximate download size |
|-------|--------------------------|
| Tiny  | ~75 MB |
| Base  | ~145 MB |
| Small | ~465 MB |
| Medium (recommended) | ~1.5 GB |
| Large v3 | ~3.1 GB |

Speaker diarization models (pyannote.audio) are downloaded separately on first use after HuggingFace licence acceptance — approximately **1–2 GB** additional.

**Ensure a stable internet connection is available on first launch.** Subsequent launches use the locally cached models and do not require internet access (unless Google Translate is enabled).

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

---

## Deutsch

Erste stabile Version des Spracherkennungsprogramms. Die Anwendung wandelt gesprochene Sprache in Text um, identifiziert einzelne Sprecher, übersetzt das Ergebnis optional und gibt die Ausgabe in mehreren konfigurierbaren Formaten aus — alles lokal unter Windows mit GPU-Beschleunigung.

### ⚠️ Wichtig: Erkennungsmodelle sind nicht enthalten

Das Installationsprogramm enthält **keine** Spracherkennungs- oder Sprecher-Diarisierungsmodelle. Beim **ersten Start** lädt die Anwendung das ausgewählte Whisper-Modell aus dem Internet herunter:

| Modell | Ungefähre Download-Größe |
|--------|--------------------------|
| Tiny   | ~75 MB |
| Base   | ~145 MB |
| Small  | ~465 MB |
| Medium (empfohlen) | ~1,5 GB |
| Large v3 | ~3,1 GB |

Sprecher-Diarisierungsmodelle (pyannote.audio) werden nach der HuggingFace-Lizenzakzeptanz beim ersten Einsatz separat heruntergeladen — ca. **1–2 GB** zusätzlich.

**Stellen Sie beim ersten Start eine stabile Internetverbindung sicher.** Nachfolgende Starts verwenden die lokal gespeicherten Modelle und benötigen keinen Internetzugang (sofern Google Übersetzer nicht aktiviert ist).

---

## Español

Primera versión estable del Programa de Reconocimiento de Voz. La aplicación convierte el audio hablado en texto, identifica hablantes individuales, traduce el resultado opcionalmente y entrega la salida en múltiples formatos configurables — todo ejecutándose localmente en Windows con aceleración GPU.

### ⚠️ Importante: los modelos de reconocimiento no están incluidos

El instalador **no incluye** modelos de reconocimiento de voz ni de diarización de hablantes. En el **primer inicio**, la aplicación descarga el modelo Whisper seleccionado desde internet:

| Modelo | Tamaño de descarga aproximado |
|--------|-------------------------------|
| Tiny   | ~75 MB |
| Base   | ~145 MB |
| Small  | ~465 MB |
| Medium (recomendado) | ~1,5 GB |
| Large v3 | ~3,1 GB |

Los modelos de diarización de hablantes (pyannote.audio) se descargan por separado en el primer uso tras aceptar la licencia de HuggingFace — aproximadamente **1–2 GB** adicionales.

**Asegúrese de tener una conexión a internet estable en el primer inicio.** Los inicios posteriores utilizan los modelos almacenados localmente y no requieren acceso a internet (a menos que Google Translate esté habilitado).

---

## Suomi

Puhentunnistusohjelman ensimmäinen vakaa julkaisu. Sovellus muuntaa puhutun äänen tekstiksi, tunnistaa yksittäiset puhujat, kääntää tuloksen valinnaisesti ja tuottaa tulosteet useissa määritettävissä muodoissa — kaikki paikallisesti Windows-ympäristössä GPU-kiihdytyksellä.

### ⚠️ Tärkeää: tunnistusmallit eivät sisälly pakettiin

Asennusohjelma **ei sisällä** puheentunnistus- tai puhujan diarisointimalleja. **Ensimmäisellä käynnistyskerralla** sovellus lataa valitun Whisper-mallin internetistä:

| Malli | Arvioitu latauskoko |
|-------|---------------------|
| Tiny  | ~75 Mt |
| Base  | ~145 Mt |
| Small | ~465 Mt |
| Medium (suositeltu) | ~1,5 Gt |
| Large v3 | ~3,1 Gt |

Puhujan diarisointimallit (pyannote.audio) ladataan erikseen ensimmäisellä käyttökerralla HuggingFace-lisenssihyväksynnän jälkeen — noin **1–2 Gt** lisää.

**Varmista vakaa internetyhteys ensimmäisellä käynnistyskerralla.** Seuraavat käynnistykset käyttävät paikallisesti tallennettuja malleja eivätkä vaadi internet-yhteyttä (ellei Google Translate ole käytössä).

---

## Русский

Первый стабильный выпуск программы распознавания речи. Приложение преобразует устную речь в текст, идентифицирует отдельных говорящих, при необходимости переводит результат и выводит данные в нескольких настраиваемых форматах — всё это работает локально в Windows с аппаратным ускорением GPU.

### ⚠️ Важно: модели распознавания не включены в установщик

Установщик **не включает** модели распознавания речи и диаризации говорящих. При **первом запуске** приложение загружает выбранную модель Whisper из интернета:

| Модель | Приблизительный размер загрузки |
|--------|----------------------------------|
| Tiny   | ~75 МБ |
| Base   | ~145 МБ |
| Small  | ~465 МБ |
| Medium (рекомендуется) | ~1,5 ГБ |
| Large v3 | ~3,1 ГБ |

Модели диаризации говорящих (pyannote.audio) загружаются отдельно при первом использовании после принятия лицензии HuggingFace — дополнительно около **1–2 ГБ**.

**При первом запуске убедитесь в наличии стабильного подключения к интернету.** При последующих запусках используются локально кэшированные модели, доступ к интернету не требуется (если не включён Google Translate).

---

## 简体中文

语音识别程序的首个稳定版本。应用程序将语音音频转换为文本，识别各个说话人，可选地翻译结果，并以多种可配置格式输出——全部在 Windows 上本地运行，支持 GPU 加速。

### ⚠️ 重要：安装包不含识别模型

安装程序**不包含**语音识别或说话人分离模型。**首次启动**时，应用程序将从互联网下载所选的 Whisper 模型：

| 模型 | 近似下载大小 |
|------|------------|
| Tiny | ~75 MB |
| Base | ~145 MB |
| Small | ~465 MB |
| Medium（推荐） | ~1.5 GB |
| Large v3 | ~3.1 GB |

说话人分离模型（pyannote.audio）在接受 HuggingFace 许可后首次使用时单独下载——额外约 **1–2 GB**。

**请确保首次启动时有稳定的网络连接。** 后续启动将使用本地缓存的模型，无需互联网访问（除非启用了 Google 翻译）。

---

## 繁體中文

語音辨識程式的首個穩定版本。應用程式將語音音頻轉換為文字，識別個別說話者，可選地翻譯結果，並以多種可配置格式輸出——全部在 Windows 上本地執行，支援 GPU 加速。

### ⚠️ 重要：安裝包不含辨識模型

安裝程式**不包含**語音辨識或說話者分離模型。**首次啟動**時，應用程式將從網際網路下載所選的 Whisper 模型：

| 模型 | 近似下載大小 |
|------|------------|
| Tiny | ~75 MB |
| Base | ~145 MB |
| Small | ~465 MB |
| Medium（推薦） | ~1.5 GB |
| Large v3 | ~3.1 GB |

說話者分離模型（pyannote.audio）在接受 HuggingFace 授權後首次使用時單獨下載——額外約 **1–2 GB**。

**請確保首次啟動時有穩定的網路連線。** 後續啟動將使用本地快取的模型，無需網際網路存取（除非啟用了 Google 翻譯）。

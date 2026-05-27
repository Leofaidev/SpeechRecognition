# Spracherkennungsprogramm

Eine lokal ausgeführte, GPU-beschleunigte Desktop-Anwendung zur Spracherkennung für Windows. Wandelt gesprochene Audiodaten in Text um, identifiziert einzelne Sprecher, übersetzt das Ergebnis optional und liefert die Ausgabe in mehreren konfigurierbaren Formaten.

**Version 1.0** — veröffentlicht am 21.05.2026

[English](README.md) | [Español](README.es.md) | [Suomi](README.fi.md) | [Русский](README.ru.md) | [简体中文](README.zh_CN.md) | [繁體中文](README.zh_TW.md)

---

## Funktionen

- Sprache-zu-Text über faster-whisper (CUDA-beschleunigt; CPU-Fallback unterstützt)
- Sprecherdiarisierung über pyannote.audio — bis zu 10 simultane Sprecher
- Lokale Übersetzung (Helsinki-NLP OPUS-MT, offline) oder online (Google Übersetzer)
- Ausgabeformate: Klartext, DOCX, SRT-Untertitel, JSON, Zwischenablage
- Batch-Dateiverarbeitung mit FIFO-Warteschlange
- Sprachprofil-Bibliothek: Speicherung und Identifizierung benannter Sprecher über Sitzungen hinweg
- Verwaltung von Sprechergruppen für kontextspezifische Identifizierung
- Konfigurierbare globale Tastenkürzel (systemweit, auch bei minimiertem Fenster)
- Reguläre und Kurzaufnahme-Sitzungsmodi
- GUI (CustomTkinter) und vollständiger CLI-Modus
- Systemtray-Integration mit Benachrichtigungen
- Sitzungsverlauf mit nachträglicher Ausgaberegeneration
- Sicherung und Wiederherstellung aller Benutzerdaten

---

## Systemanforderungen

| Anforderung | Details |
|-------------|---------|
| Betriebssystem | Windows 10 oder 11, 64-Bit |
| GPU | NVIDIA-GPU mit CUDA empfohlen (RTX 3060 Ti oder besser); CPU-Fallback unterstützt |
| RAM | Mindestens 4 GB; 8 GB empfohlen für Dateien ab 30 Minuten |
| Speicher | 10 GB frei (enthält alle Whisper-Modellgrößen und OPUS-MT-Sprachpaare) |
| VLC | Erforderlich für die Audiowiedergabe — Installer lädt VLC automatisch herunter, falls nicht vorhanden |
| FFmpeg | Erforderlich für MP4/AVI-Extraktion — muss bei Ausführung aus dem Quellcode im PATH sein |

---

## Schnellstart — Installer

1. `wsp_setup.exe` aus dem [neuesten GitHub-Release](../../releases/latest) herunterladen.
2. Installer ausführen und dem Assistenten folgen:
   - Ein Whisper-Modell auswählen (Medium wird empfohlen).
   - HuggingFace-pyannote-Lizenz akzeptieren, wenn Sprecheridentifizierung gewünscht wird.
3. **Spracherkennungsprogramm** über die Desktop-Verknüpfung oder das Startmenü starten.
4. Ein Eingabegerät auswählen oder eine Audiodatei in die Batch-Warteschlange ziehen und **Starten** drücken.

---

## Schnellstart — Aus dem Quellcode

```bat
git clone https://github.com/Leofaidev/SpeechRecognition.git
cd SpeechRecognition
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

> **Hinweis:** PyAudio benötigt Microsoft C++ Build Tools und PortAudio über vcpkg vor `pip install`.
> Siehe die Kommentare am Anfang von `requirements.txt` für Schritt-für-Schritt-Anweisungen.
> FFmpeg muss systemweit installiert und im PATH sein.

---

## Kommandozeilenverwendung

```bat
wsp.exe --input interview.mp3 --output-format txt json
wsp.exe --input a.mp3 b.wav --output-folder C:\Output --speaker-group "Interviewers"
wsp.exe --backup C:\Backups\wsp_backup.zip
wsp.exe --help
```

Vollständige Parameterreferenz und Exit-Codes siehe [docs/CLI.md](docs/CLI.md).

---

## Benutzeroberflächensprachen

Englisch, Deutsch, Spanisch, Finnisch, Russisch, Vereinfachtes Chinesisch, Traditionelles Chinesisch.

> Russische und chinesische Übersetzungen sind automatisiert. Überprüfung durch Muttersprachler steht noch aus.

---

## Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| [docs/Specification.md](docs/Specification.md) | Vollständige technische Spezifikation (v1.0) |
| [docs/WorkPlan.md](docs/WorkPlan.md) | Phasenweiser Arbeitsplan (Phasen 0–9) |
| [docs/CLI.md](docs/CLI.md) | Kommandozeilen-Parameterreferenz |
| [docs/BUILD.md](docs/BUILD.md) | Installationserstellungsanweisungen (aus dem Quellcode) |
| [docs/SPEAKER_JSON_SCHEMA.md](docs/SPEAKER_JSON_SCHEMA.md) | Format der Sprachprofil-`speaker.json` |
| [docs/SESSION_JSON_SCHEMA.md](docs/SESSION_JSON_SCHEMA.md) | JSON-Format des Sitzungsverlaufs |
| [docs/RELEASE_NOTES_v1.0.md](docs/RELEASE_NOTES_v1.0.md) | Release-Notes v1.0 |

---

## Bibliotheken

Alle Bibliotheken sind kostenlos und Open-Source. Pinned-Versionen siehe `requirements.txt`.

| Bibliothek | Funktion | Lizenz |
|------------|----------|--------|
| faster-whisper | Sprache-zu-Text und Spracherkennung | MIT |
| pyannote.audio | Sprecherdiarisierung (HuggingFace-Lizenz erforderlich) | MIT |
| CustomTkinter | Grafische Benutzeroberfläche | MIT |
| pyaudio | Mikrofon- und Webcam-Audioaufnahme | MIT |
| OpenCV | Webcam-Videostream-Zugriff | Apache 2.0 |
| keyboard | Globale Tastenkürzel | MIT |
| transformers + sentencepiece | Lokale Übersetzung Helsinki-NLP OPUS-MT | Apache 2.0 |
| python-vlc | Audio-/Videowiedergabe | LGPL 2.1 |
| python-docx | DOCX-Ausgabe | MIT |
| PyInstaller | Anwendungsbündelung | GPL + Bootloader-Ausnahme |
| Inno Setup | Windows-Installer (separates Tool) | Inno Setup Lizenz |
| PyTorch | Deep-Learning-Laufzeit | BSD 3-Clause |

> **HuggingFace-Lizenz:** pyannote.audio erfordert die Annahme der HuggingFace-Modelllizenz.
> Wenn nicht akzeptiert, ist die Sprecheridentifizierung deaktiviert und alle Sprecher werden als Unbekannt bezeichnet.

---

## Mitwirken / Probleme

Dies ist ein privates Repository. Um einen Fehler zu melden oder eine Funktion anzufordern, öffnen Sie ein Issue auf GitHub.

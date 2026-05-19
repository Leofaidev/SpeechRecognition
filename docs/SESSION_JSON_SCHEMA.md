# Session History JSON Schema

After every processing session (file, batch, or microphone/webcam), the full transcription result is saved as a JSON file in the `sessions/` subfolder of the installation directory. This document defines the schema.

**Spec reference:** Sections 11.1, 4.3, 8.4

---

## Schema

```json
{
  "session_id": "3f2a1b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c",
  "created_at": "2026-05-19T12:00:00Z",
  "source_type": "file",
  "source_path": "C:\\Users\\Leo1\\Documents\\interview.mp3",
  "speaker_group": "Group 1",
  "output_files": [
    "C:\\Users\\Leo1\\AppData\\Local\\SpeechRecognitionProgram\\output\\interview_WSP.txt",
    "C:\\Users\\Leo1\\AppData\\Local\\SpeechRecognitionProgram\\output\\interview_WSP.json"
  ],
  "last_clipboard_text": "Hello, this is the most recently copied text.",
  "output_outdated": false,
  "segments": [
    {
      "index": 0,
      "speaker_name": "John Smith",
      "start_time": "00:00:01,500",
      "end_time": "00:00:05,200",
      "language": "English",
      "text": "Hello, my name is John Smith.",
      "translated_text": null,
      "transcription_confidence": 0.98765,
      "speaker_confidence": 0.9234,
      "bad_audio": false,
      "output_outdated": false
    },
    {
      "index": 1,
      "speaker_name": "Speaker 2",
      "start_time": "00:00:06,000",
      "end_time": "00:00:09,800",
      "language": "English",
      "text": "XXXXX XXXXX this question.",
      "translated_text": null,
      "transcription_confidence": 0.31200,
      "speaker_confidence": 0.4100,
      "bad_audio": true,
      "output_outdated": false
    }
  ]
}
```

---

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string (UUID v4) | Unique identifier for this session. Used by `--regenerate-output --session`. |
| `created_at` | string (ISO 8601 UTC) | Timestamp when the session was saved. |
| `source_type` | string | `"file"`, `"batch"`, `"microphone"`, or `"webcam"`. |
| `source_path` | string or null | Absolute path to the source file. `null` for microphone/webcam sessions. For batch sessions, the path of the first file in the queue. |
| `speaker_group` | string | Name of the active voice library group at the time of processing. |
| `output_files` | array of strings | Absolute paths to all output files produced by this session. Empty if no files were written. |
| `last_clipboard_text` | string or null | The most recently written clipboard text for this session (updated on each clipboard write). `null` if clipboard was never written. |
| `output_outdated` | boolean | `true` if any speaker profile referenced in `segments` has been edited since this session was saved. Set by the profile editor; never reset automatically. |
| `segments` | array | Ordered list of transcribed segment objects (see below). |

---

## Segment Fields

| Field | Type | Description |
|-------|------|-------------|
| `index` | integer | Zero-based segment index within the session. |
| `speaker_name` | string | Final speaker label after retroactive relabelling. May be `"Speaker N"` for unidentified speakers or `"Unknown"` when diarization is disabled. |
| `start_time` | string | Segment start time in `HH:MM:SS,mmm` format, from the beginning of the file or recording. |
| `end_time` | string | Segment end time in `HH:MM:SS,mmm` format. |
| `language` | string or null | Detected source language name (e.g. `"English"`, `"Finnish"`). `null` when language detection was not run. |
| `text` | string | Recognised text after substitution dictionary has been applied. Unrecognised tokens in bad-audio segments are replaced with `XXXXX`. |
| `translated_text` | string or null | Translated text if translation was enabled; otherwise `null`. |
| `transcription_confidence` | number | Whisper per-segment confidence, decimal to 5 places (0.00000–1.00000). |
| `speaker_confidence` | number | pyannote.audio speaker match confidence, decimal to 4 places (0.0000–1.0000). `0.0` when speaker identification was not run. |
| `bad_audio` | boolean | `true` if `no_speech_prob > 0.6` for this segment (Spec 3.4.a). |
| `output_outdated` | boolean | `true` if the speaker profile for `speaker_name` has been edited since this session was saved. |

---

## Output Regeneration

When `--regenerate-output` is called (CLI) or the user clicks "Regenerate Output" in the Session History panel, the application loads the `segments` array from this file and applies the **current** output content configuration. It does not re-run audio processing.

Regenerated output files follow the `_WSP` naming convention with numeric suffixes on collision (e.g. `interview_WSP_2.txt`).

---

## File Location

```
<install_dir>/sessions/<session_id>.json
```

Sessions are retained indefinitely. There is no automatic deletion. The user may delete individual sessions from the Session History panel or via the file system.

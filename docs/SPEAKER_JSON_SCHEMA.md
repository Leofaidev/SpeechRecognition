# speaker.json Schema

Each speaker profile subfolder in the voice library contains a `speaker.json` file. This document defines the schema and all field semantics.

**Spec reference:** Section 4.5.d

---

## Schema

```json
{
  "last_name": "Smith",
  "first_name": "John",
  "middle_name": "",
  "nickname": "",
  "organisation": "Acme Corp",
  "position": "Director",
  "note": "Internal use only — never appears in output",
  "creation_date": "2026-05-19T12:00:00Z",
  "model_checksum": "sha256:a3f1c2b4d5e6f7890123456789abcdef0123456789abcdef0123456789abcdef01",
  "sample_count": 2,
  "samples": [
    "sample_001.mp3",
    "sample_002.mp3"
  ],
  "groups": [
    "Group 1",
    "Management"
  ],
  "low_confidence": false
}
```

---

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `last_name` | string | No | Speaker last name. Stored with original characters. |
| `first_name` | string | No | Speaker first name. |
| `middle_name` | string | No | Speaker middle name. |
| `nickname` | string | No | Speaker nickname. The reserved prefix `#` (e.g. `#001`) is used for auto-assigned IDs when all name fields are empty. |
| `organisation` | string | No | Organisation. |
| `position` | string | No | Position or role. |
| `note` | string | No | Internal note. Never included in any output. |
| `creation_date` | string (ISO 8601) | Yes | UTC timestamp when the profile was created. |
| `model_checksum` | string | Yes | SHA-256 checksum of the pyannote.audio model files at the time of the most recent successful embedding generation, prefixed with `sha256:`. |
| `sample_count` | integer | Yes | Number of MP3 samples used in the most recent embedding generation. |
| `samples` | array of strings | Yes | List of MP3 sample filenames in sequential order (e.g. `sample_001.mp3`). |
| `groups` | array of strings | Yes | Names of all voice library groups this speaker belongs to. May be empty. |
| `low_confidence` | boolean | Yes | `true` if any sample is shorter than 10 seconds. Displayed as a visual indicator in the profile list. |

---

## Subfolder Name

The subfolder containing this file is named by joining `last_name`, `first_name`, `middle_name`, and `nickname` with underscores. Characters invalid in Windows folder names are replaced with `_`; the original values are preserved in this JSON.

Examples:

| last_name | first_name | middle_name | nickname | Folder name |
|-----------|------------|-------------|----------|-------------|
| Smith | John | | | `Smith_John__` |
| Иванов | Иван | Петрович | | `Иванов_Иван_Петрович_` |
| | | | | `____001` (auto-ID; nickname = `#001`) |

---

## Auto-Assigned Numeric ID

When all four name fields are empty, a unique three-digit numeric ID is appended to the folder name (e.g. `____001`). The ID is stored in the `nickname` field with the `#` prefix (`"nickname": "#001"`). When the user fills in any real name field via the profile editor, the auto-assigned nickname is cleared automatically.

---

## Model Checksum and Retraining

On every startup the application computes the SHA-256 checksum of the current pyannote.audio model files and compares it against `model_checksum` in each profile. A mismatch triggers the voice library retraining workflow (Spec Section 4.6). After successful retraining, `model_checksum` and `sample_count` are updated.

# Speech Recognition Program — CLI Reference

**Version 1.0**

All command-line output (errors, warnings, summaries) is always in English, regardless of the configured UI language. The GUI is never launched in CLI mode. Exit code `0` on success; non-zero on any error.

Parameters follow standard Windows conventions: double-dash long form (`--param`), single-dash short alias where noted.

---

## Synopsis

```
wsp.exe [GLOBAL OPTIONS] [OPERATION] [OPERATION OPTIONS]
```

---

## Global Options

| Parameter | Alias | Description |
|-----------|-------|-------------|
| `--help` | `-h` | Print all parameters with descriptions and examples, then exit 0. |
| `--output-folder <path>` | `-o` | Folder for all output files. Defaults to last saved value; falls back to the installation folder. |
| `--output-format <fmt ...>` | `-f` | One or more output formats: `txt`, `docx`, `srt`, `json`. Defaults to last saved value. |
| `--source-language <lang>` | `-l` | Source language code (e.g. `en`, `fi`, `ru`). Omit for automatic detection. |
| `--target-language <lang>` | `-t` | Translation target language. Omit to disable translation. Supported: `en`, `es`, `fi`, `ru`, `zh-Hans`, `zh-Hant`. |
| `--speaker-group <name>` | `-g` | Name of the voice library group to use for identification. Defaults to last saved group. |
| `--input-device <name>` |  | Partial, case-insensitive device name for microphone/webcam input. First match is used; lists all devices on no match. |
| `--translation-engine <engine>` |  | `opus-mt` (default, local) or `google` (online). |

---

## Operations

### Batch Processing

Process one or more audio files through the full pipeline (diarization → transcription → substitution → translation → output).

```
wsp.exe --input <file> [<file> ...] [GLOBAL OPTIONS]
```

| Parameter | Alias | Description |
|-----------|-------|-------------|
| `--input <file ...>` | `-i` | One or more input files (MP3, WAV, MP4, AVI). **Mandatory** when no saved config exists. |

**Examples:**

```bat
wsp.exe --input interview.mp3
wsp.exe --input a.mp3 b.wav c.avi --output-format txt json --output-folder C:\Output
wsp.exe -i recording.wav -l fi -t en -f txt srt
```

---

### Voice Profile Management

#### Create a profile

Extract a 10-second voice sample from an audio file and add it to the library.

```
wsp.exe --profile-create --audio <path> --lastname <name> [OPTIONS]
```

| Parameter | Description |
|-----------|-------------|
| `--profile-create` | Trigger profile creation. |
| `--audio <path>` | Source audio file (MP3, WAV, MP4, AVI). **Mandatory.** |
| `--lastname <name>` | Speaker last name. |
| `--firstname <name>` | Speaker first name. |
| `--middlename <name>` | Speaker middle name. |
| `--nickname <name>` | Speaker nickname. |
| `--organisation <name>` | Organisation. |
| `--position <name>` | Position/role. |
| `--note <text>` | Internal note (never appears in output). |

At least one of `--lastname`, `--firstname`, `--nickname` is recommended; all name fields are optional.

**Example:**

```bat
wsp.exe --profile-create --audio sample.mp3 --lastname Smith --firstname John --organisation "Acme Corp"
```

#### Delete a profile

```
wsp.exe --profile-delete --name "<name>"
```

`<name>` is the full folder name of the profile (e.g. `Smith_John__`).

#### Rename a profile

```
wsp.exe --profile-rename --name "<current>" --new-name "<new>"
```

---

### Dictionary Management

#### Export dictionary

```
wsp.exe --dict-export "<path>"
```

Writes the current substitution dictionary to a CSV file at `<path>`.

#### Import dictionary

```
wsp.exe --dict-import "<path>"
```

Reads a CSV file and adds new entries. Conflicting entries (same source word) are rejected. Prints a summary to stdout:

```
Imported: 8 entries added, 2 rejected.
Rejected source words: "gonna", "wanna"
```

---

### Backup and Restore

#### Create a backup

```
wsp.exe --backup "<path>"
```

Creates a ZIP archive containing all user data (config, dictionary, voice library, groups, output config, session history) at `<path>`.

#### Restore a backup

```
wsp.exe --restore "<path>"
```

Before restoring, automatically creates a safety backup of the current state and prints its location to stdout. Then replaces all current data with the archive contents.

```
Safety backup created at: C:\Users\Leo1\AppData\Local\SpeechRecognitionProgram\backups\safety_20260519_120000.zip
Restoring from: C:\Backups\wsp_backup.zip
Restore complete.
```

---

### Session History

#### List all sessions

```
wsp.exe --list-sessions
```

Prints a table of all stored sessions:

```
ID                                   Date                 Source
------------------------------------+--------------------+---------
3f2a1b4c-...                         2026-05-19 12:00:00  file
a1b2c3d4-...                         2026-05-18 09:30:00  microphone
```

#### Regenerate output for a session

```
wsp.exe --regenerate-output --session "<session_id>" --output-folder "<path>"
```

Re-writes output files for the specified session using the current output content configuration. Files are named with the standard `_WSP` convention; numeric suffixes are appended on collision.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Unrecognised parameter or invalid argument |
| `2` | Missing mandatory input files |
| `3` | Input file not found or unreadable |
| `4` | Output folder not writable |
| `5` | Session ID not found |
| `10` | Translation service error (Google Translate) |
| `20` | Voice library error (missing files, corrupt profile) |

---

## Notes

- Parameters omitted from the command line default to the last saved session configuration.
- The `--input` parameter is the only mandatory parameter when no saved configuration exists.
- If `--speaker-group` names a group that does not exist, the application exits with a specific error listing all available groups.
- If the HuggingFace licence has not been accepted, a warning is printed and processing continues with all speakers labelled `Unknown`.
- Hotkeys are completely disabled in CLI mode.
- The completion sound and tray notifications are suppressed in CLI mode.

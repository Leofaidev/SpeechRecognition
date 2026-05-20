# Wireframe V1 — Minimalist Design

**Spec references:** 12.4, 12.6.d, 12.8  
**PDF file:** `wireframe_v1_minimalist.pdf` (12 pages)

---

## Design Philosophy

Content leads; chrome follows. Every pixel of decoration must justify its existence. The interface recedes so the transcription text commands attention. Visual hierarchy is communicated solely through spacing, weight, and a single accent colour. No shadows, no gradients, no rounded corners. This design targets power users who want zero visual noise during long transcription sessions.

---

## Colour Palette

| Role | Hex | Usage |
|------|-----|-------|
| Background | `#F9F9F9` | Page/window fill |
| Window | `#FFFFFF` | Panel content area |
| Title bar | `#3D3D3D` | Top window chrome |
| Toolbar | `#F2F2F2` | Secondary control rows |
| Sidebar | `#F7F7F7` | Settings nav, voice-profile sidebar |
| Primary | `#2980B9` | Primary buttons, active states, links |
| Accent (danger) | `#C0392B` | Recording indicator, delete actions |
| Success | `#27AE60` | OK states, confirmation |
| Warning | `#E67E22` | Outdated indicator, conflict warning |
| Text | `#2C2C2C` | Primary text |
| Text dim | `#AAAAAA` | Labels, placeholders, secondary info |
| Border | `#DEDEDE` | Element outlines, dividers |
| Input bg | `#FFFFFF` | Text fields, dropdowns, list boxes |
| Selected | `#D6EAF8` | Selected list item highlight |
| Annotation | `#C0392B` | Element callout circles in wireframe |

## Typography

| Role | Size | Weight | Family |
|------|------|--------|--------|
| Panel heading | 9 pt | Bold | Sans-serif |
| Body / labels | 7.2 pt | Regular | Sans-serif |
| Small / captions | 6 pt | Regular | Sans-serif |
| Callout tags | 5.2 pt | Bold | Sans-serif |
| Hotkey display | 7.2 pt | Regular | Monospace |

## Geometry

- Corner radius: **0** (all elements are sharp-cornered rectangles)
- Border width: 0.65 px
- No drop shadows
- No gradients

---

## Page 1: Main Window — Regular Mode

### Layout

```
┌─ Title bar ────────────────────────────────── [●][─][✕] ─┐
│ Speech Recognition Program                                  │
├─ Nav ────────────────────────────────────────────────────── │
│ ◀ Main Window — Regular Mode                               │
├──────────────────────────────────────────────────────────── │
│ Input: [Microphone (Realtek HD) ▾]  [▐▐▐▐░░] ● REC        │
│                        Mode: [● Regular] [Short Session]   │
├──────────────────────────────────────────────────────────── │
│ Speaker Group: [Group 1 ▾]                                 │
├──────────────────────────────────────────────────────────── │
│ File: [▓▓▓▓▓▓░░░░ 45%]          Queue: [▓░░░░ 1/5 files]  │
├──────────────────────────────────────────────────────────── │
│                                                              │
│  Speaker 1 (00:00:01,500 – 00:00:05,200)                   │
│  Hello, my name is John Smith. How are you today?           │
│ ─────────────────────────────────────────────              │
│  Speaker 2 (00:00:06,000 – 00:00:09,800)                   │
│  I'm doing well, thank you. Let's discuss…                 │
│                                                              │
├──────────────────────────────────────────────────────────── │
│ [▶ Play]  [────────●─────────────────]  01:23 / 05:47      │
└──────────────────────────────────────────────────────────── ┘
```

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Device Dropdown | Dropdown | Selects the audio input device from a list of all pyaudio-enumerated input devices. Populated by `platforms.windows.DeviceEnum.list_devices()`. | `onChange` → update active capture source; triggers `audio.device` reconfiguration | `normal`, `disabled` (during active recording or processing) |
| 2 | Signal Meter | VU Meter | Animated bar-graph showing real-time audio input level. 12 bars, colour-coded: green (0–60%), amber (60–85%), red (85–100%). Updates at ~20 Hz from the audio capture stream. | Real-time animation; no user interaction | `active` (during capture), `inactive` (flat when not recording) |
| 3 | Recording Indicator | Status LED | Red filled circle labelled "REC" when actively recording. Green circle labelled "READY" when idle. The colour and label change atomically. | No direct interaction; state is driven by the recording pipeline | `ready` (green), `recording` (red), `processing` (amber, pulsing) |
| 4 | Mode Toggle | Toggle Group | Two-button toggle: "Regular" / "Short Session". Selecting Short Session switches the main content area to the two-field form (see Page 2). | `onClick Regular` → show transcript display, hide two-field form; `onClick Short Session` → show two-field form, hide transcript display | One button always active |
| 5 | Speaker Group Dropdown | Dropdown | Selects the active voice-profile group used for speaker identification. Populates from `library.groups`. Default: "Group 1 (All)". | `onChange` → update active group in `session.manager`; takes effect on the next recording | `normal`, `disabled` during processing |
| 6 | File Progress Bar | Progress Bar | Shows percentage completion of the current file being processed (diarization + transcription pipeline). Hidden when not processing. | Read-only | `hidden`, `running` (animated fill), `complete` (full fill) |
| 7 | Queue Progress | Progress Bar | Shows "N / M files" for batch mode. Hidden in single-file mode. | Read-only | `hidden` (single-file), `visible` (batch) |
| 8 | Transcript Display Area | Scrollable Text Area | Main output area. Displays speaker segments in order: speaker name (coloured by speaker ID), timestamp range, transcribed text. Scrolls automatically as segments arrive. Segments are clickable — clicking a timestamp jumps VLC playback to that position. | `onClick segment timestamp` → seek playback; `Ctrl+A` → select all text | `empty`, `streaming` (segments arriving in real time), `complete`, `outdated` (dim if speaker profiles edited since session) |
| 9 | Play / Pause Button | Button | Starts or pauses VLC playback of the currently loaded source file. Label toggles between "▶ Play" and "⏸ Pause". Disabled during active recording. | `onClick` → toggle playback via python-vlc | `enabled`, `disabled` (during recording or when no file loaded) |
| 10 | Seek Slider | Slider | Horizontal track with draggable circle handle. Shows current playback position within the file. Dragging or clicking jumps to that position. | `onDrag` / `onClick` → seek VLC to position; updates timestamp display | `enabled`, `disabled` |
| 11 | Timestamp Display | Label | Shows "current / total" as `MM:SS` or `HH:MM:SS`. Updated every 250 ms during playback. | Read-only | — |

---

## Page 2: Main Window — Short Session Mode (Amendment)

### Layout

Top toolbar identical to Regular mode (device, signal meter, REC indicator, mode toggle — showing "Short Session" active).

```
┌── Two-field form ──────────────────────────────────────────┐
│  Transcription                        [Translate & Copy]   │
│ ┌─────────────────────────────────┐                        │
│ │ Hello, this is the transcribed  │                        │
│ │ speech text…                    │                        │
│ └─────────────────────────────────┘                        │
│ ─────────────────────────────────────────────              │
│  Translation                          [Save to Clipboard]  │
│ ┌─────────────────────────────────┐                        │
│ │ Tässä on käännetty teksti…      │                        │
│ └─────────────────────────────────┘                        │
└────────────────────────────────────────────────────────────┘
```

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Mode Toggle (Short Session active) | Toggle Group | Same control as Page 1. In this state "Short Session" is the active button. | `onClick Regular` → switch back to transcript mode | Active = Short Session |
| 2 | Transcription Field | Multiline Text Field | Editable text area populated automatically after the pipeline completes. The user can edit the text before copying. Supports OS-level undo/redo (Ctrl+Z / Ctrl+Y) independently of other history stacks. Cleared at the start of each new recording. | `onTextChange` → marks content as "user-edited"; `Ctrl+Z` → undo text edit; `Ctrl+Y` → redo | `empty` (before first recording), `populated`, `user-edited` |
| 3 | Translate & Copy Button | Button | Primary action. Label is "Translate & Copy" when translation is enabled; changes to "Copy to clipboard" when translation is disabled. **Translate & Copy**: sends field 1 content to `translation.engine`, writes result to field 2, writes result to clipboard. **Copy**: copies field 1 content directly to clipboard. Always updates the session `last_clipboard_text`. | `onClick` → translate if enabled → write to field 2 → write to clipboard → update session record | `translate-mode`, `copy-mode` (label changes) |
| 4 | Translation Field | Multiline Text Field | Editable text area populated by the pipeline's automatic translation or by clicking "Translate & Copy". Supports OS-level undo/redo independently of field 1. **Hidden** when translation is disabled — field 1 expands to fill its space. Cleared at the start of each new recording. | `onTextChange` → marks content as user-edited; `Ctrl+Z` / `Ctrl+Y` | `visible` (translation on), `hidden` (translation off), `empty`, `populated` |
| 5 | Save to Clipboard Button | Button | Copies the current content of field 2 to the clipboard. Updates `last_clipboard_text` in the session record. Visible only when translation is enabled and field 2 is visible. | `onClick` → write field 2 to clipboard → update session record | `visible` (translation on), `hidden` (translation off) |

**Dynamic layout rules:**
- Translation **disabled**: field 2 and button 5 animate to zero height and disappear; field 1 expands to fill the space; button 3 label changes to "Copy to clipboard".
- Translation **re-enabled**: reverse animation; both fields visible; button 3 label reverts.
- Both fields are cleared (emptied) each time the start hotkey is pressed.
- The session record is updated on every clipboard write (automatic write after pipeline, button 3 click, button 5 click); `last_clipboard_text` holds the most recent write.

---

## Page 3: Settings

### Layout

Left sidebar (categories) + right form area. Active category: **Transcription**.

### Sidebar Categories

`Audio & Input` | `Transcription` (active) | `Translation` | `Output` | `Advanced` | `About`

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Source Language Dropdown | Dropdown | Language to expect in the audio. "Auto-detect" uses faster-whisper's built-in language detection. Fixed language skips detection and may improve accuracy. | `onChange` → persist to `config.store`; takes effect on next recording | Any language faster-whisper supports |
| 2 | Target Language Dropdown | Dropdown | Language to translate into. Only relevant when translation is enabled. | `onChange` → persist to config | Any language supported by active translation engine |
| 3 | Whisper Model Dropdown | Dropdown | Selects the faster-whisper model size: tiny / base / small / medium / large. Larger = more accurate, slower, more VRAM. Model files are **not** bundled; they are downloaded by the installer. | `onChange` → warns if model file absent; persist to config | Any of the 5 sizes |
| 4 | Bad Audio Threshold Slider | Slider | Sets the `no_speech_prob` threshold above which a segment is marked `bad_audio=true` (Spec 3.4.a). Range: 0.0–1.0, default 0.6. Segments above threshold are shown in a muted colour and text is replaced with `XXXXX`. | `onDrag` → live preview of threshold value; `onRelease` → persist to config | 0.0–1.0 |
| 5 | Min Profile Samples | Integer Input | Minimum number of confirmed audio samples required before a voice profile is usable for speaker identification. Default: 10. Below this count, diarization returns the raw pyannote speaker ID. | `onChange` → validate ≥ 1; persist to config | Integer ≥ 1 |
| 6 | Translation Toggle | Toggle Switch | Master on/off for translation. When off, field 2 and "Save to clipboard" button are hidden on the Short Session form; output files do not contain translated text. | `onChange` → persist to config; triggers layout update on main window | `on`, `off` |
| 7 | Auto-Start Toggle | Toggle Switch | Writes / removes a Windows `HKCU\…\Run` registry entry via `platforms.windows.AutoStart`. Takes effect immediately. | `onChange` → call `AutoStart.enable()` or `AutoStart.disable()` | `on`, `off` |
| 8 | HuggingFace Licence Button | Action + Status | Displays current licence acceptance status. If not accepted, shows the HuggingFace model page in the system browser. Once accepted, the `licence_accepted` flag is persisted in config. Without acceptance, all diarization is disabled and speakers are labelled "Unknown". | `onClick` → open browser; after returning, re-check flag | `accepted`, `not-accepted` |
| 9 | Output Folder Picker | File Path + Browse | Persistent destination folder for all output files (_WSP). Defaults to `%USERPROFILE%\Documents\Output`. The Browse button opens a standard folder picker dialog. | `onChange` → validate writable; persist to config | Valid path, invalid path (red border) |

---

## Page 4: Voice Profile Management

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Speaker List | List Box | All speakers in the library. Sorted alphabetically. Shows display name (constructed from `last_name + first_name`; falls back to `nickname`; falls back to auto-ID `#001`). Click to select; drag to a group to assign membership. | `onClick` → load speaker detail in right pane; `onDrag` → assign to dragged group | `selected`, `normal` |
| 2 | Speaker Actions | Button Group | **+ Add**: opens Speaker Labelling Prompt for a new speaker. **Rename**: opens inline rename field. **Delete**: shows confirmation dialog; deletes folder and all voice-profile data permanently. | `onClick Add` → open labelling prompt; `onClick Delete` → confirm dialog → delete profile | Rename/Delete disabled when nothing selected |
| 3 | Import / Export | Button Group | **Import**: accepts a ZIP containing a `speaker.json` + audio samples; adds speaker to library. **Export**: exports selected speaker to ZIP. | `onClick Import` → file picker → validate ZIP → copy to library; `onClick Export` → save ZIP dialog | Export disabled when nothing selected |
| 4 | Group List | List Box | All speaker groups. "Group 1 (All)" is the default group and cannot be deleted. Click selects; shows members. | `onClick` → filter speaker list to group members; highlight group | — |
| 5 | Group Actions | Button Group | **+ Add Group**: inline text prompt for group name. **Rename**: inline rename. Delete hidden (only present for non-default groups). | — | Add Group always enabled |
| 6 | Speaker Avatar | Avatar Circle | Initials-based avatar (first letter of first name + first letter of last name). No actual image is stored. Cosmetic only. | None | — |
| 7–11 | Metadata Fields | Text Inputs | First Name, Last Name, Organisation, Position, Note. All optional except at least one of (first name, last name, nickname) must be non-empty. Changes are saved on focus-out. `speaker.json` is updated immediately; `output_outdated` is set on all sessions that referenced this speaker. | `onChange` → auto-save on blur; update display name in speaker list | — |

---

## Page 5: Substitution Dictionary

The dictionary applies case-insensitive, whole-word, fnmatch-wildcard substitutions **after** transcription and **before** translation.

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Add Row | Button | Inserts a new empty row at the bottom of the table. Enters edit mode for the Source Term cell immediately. | `onClick` → append row; focus Source Term cell | — |
| 2 | Edit Row | Button | Enters edit mode for the selected row. Disabled when no row is selected. | `onClick` → enable cell editing | `enabled` (row selected), `disabled` |
| 3 | Delete Row | Button | Deletes the selected row after confirmation. | `onClick` → confirm → delete; push undo record | `enabled` (row selected), `disabled` |
| 4 | Search Box | Text Input | Filters visible rows by substring match on Source Term or Replacement columns. Does not affect the stored dictionary. | `onInput` → filter table rows live | `empty`, `filtering` |
| 5 | Import CSV | Button | Opens a file picker for a CSV file with columns: `source,replacement`. Appends all rows. Duplicates (matching source term) are overwritten with confirmation. | `onClick` → file picker → parse CSV → append/overwrite | — |
| 6 | Export CSV | Button | Saves the entire dictionary to a UTF-8 CSV file with header row `source,replacement`. | `onClick` → save dialog | — |
| 7 | Undo / Redo | Button Pair | Undo/redo for dictionary operations only (add, edit, delete, import). Independent of all other undo histories. Keyboard: Ctrl+Z / Ctrl+Y within the dictionary panel. | `onClick Undo` → revert last op; `onClick Redo` → re-apply | Undo disabled when history empty |
| 8–11 | Table Columns | Table | **#** (row index), **Source Term** (editable), **Replacement** (editable), **Flags** (read-only; shows detected match mode: `case-insensitive`, `whole-word`, `wildcard`). Rows are saved on focus-out. | `onCellEdit` → validate; auto-save | Editable cells show cursor on focus |

---

## Page 6: Batch Queue

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Queue Row | List Row | Each row shows: file name, duration (extracted by FFmpeg), status badge, per-file progress bar. Rows are immutable during processing (FIFO lock). | `onClick` → select row (no-op during processing) | `pending`, `processing`, `done`, `error` |
| 2 | Column Headers | Header Row | File Name, Duration, Status, Progress. Clicking headers has no effect (queue is unordered). | — | — |
| 3 | Status Indicator | Coloured Badge | Colour-coded: amber = Processing, grey = Pending, green = Done, red = Error. | Read-only | See above |
| 4 | Per-file Progress | Progress Bar | Animated fill during `processing` state. Shown as `XX%` text inside the bar. 0% when pending; 100% + green when done. | Read-only | `empty`, `running`, `complete` |
| 5 | Add Files | Button | Opens a multi-select file picker (MP3, WAV, MP4, AVI). Selected files are appended to the queue. | `onClick` → multi-select dialog → append to queue | `enabled` |
| 6 | Remove Selected | Button | Removes the highlighted row from the queue. Disabled during processing and when no row selected. | `onClick` → remove row | `enabled`, `disabled` |
| 7 | Clear Queue | Button | Removes all rows. Confirmation required. Disabled during processing. | `onClick` → confirm → clear all | `enabled`, `disabled` (processing) |
| 8 | Start Processing | Button | Begins FIFO processing of all pending files. Disabled while already running or queue empty. | `onClick` → lock queue; begin pipeline on first pending file | `enabled`, `disabled` |
| 9 | Stop Processing | Button | Cancels the current file at the next safe checkpoint. Already-completed files are unaffected. Shows a confirmation dialog if in the middle of a file. | `onClick` → confirm → signal stop; release lock | `enabled` (during processing), `disabled` |

---

## Page 7: Output Content Configuration

### Field Toggles

| # | Name | Description | Default |
|---|------|-------------|---------|
| 1 | Speaker Name | Include the identified speaker name before each segment in TXT/DOCX output. | ON |
| 2 | Timestamps | Include `HH:MM:SS,mmm – HH:MM:SS,mmm` range before each segment. Required for SRT output. | ON |
| 3 | Confidence Score | Append `[confidence: 0.XXXXX]` after each segment. | OFF |
| 4 | Language Label | Append `[lang: Finnish]` etc. after each segment. | OFF |
| 5 | Translated Text | Include translated text beneath each source segment (shown indented). | ON |
| 6 | Bad Audio Marker | Replace unrecognised tokens with `XXXXX` in output. If OFF, bad-audio segments are shown as-is (raw unrecognised text). | ON |

All toggles call `config.store.set(key, value)` on change and take effect on the next regeneration.

### Format Checkboxes

| # | Name | Description |
|---|------|-------------|
| 7 | TXT | Plain text file `<name>_WSP.txt` |
| 8 | DOCX | Microsoft Word document `<name>_WSP.docx` |
| 9 | SRT | SubRip subtitle file `<name>_WSP.srt` (requires Timestamps toggle ON) |
| 10 | JSON | Machine-readable session JSON `<name>_WSP.json` |
| 11 | Display | Show output in the main window transcript area |
| 12 | Clipboard | Auto-copy full output text to clipboard at end of processing |

**Element 13 — Output Folder Picker:** as described in Settings (same control, same persistence).

---

## Page 8: Hotkey Configuration

All hotkeys are **global** (work while the app is minimised to tray) and are registered via `platforms.windows.Hotkeys.register()`. `is_conflict()` checks against a static set of reserved Windows shortcuts.

### Elements

| # | Name | Key | Description | Conflict rules |
|---|------|-----|-------------|----------------|
| 1 | Start Recording | Ctrl+Shift+S | Begin a recording session | Cannot conflict with system shortcuts (Ctrl+C, Ctrl+V, Alt+F4, etc.) |
| 2 | Stop Recording | Ctrl+Shift+X | End the active recording | — |
| 3 | Push-to-Talk | F9 | Hold to record; release to stop and process. Cannot be the same as Start/Stop. | — |
| 4 | Cancel Recording | Ctrl+Shift+C | Abort without processing | — |
| 5 | Open / Show Window | Ctrl+Shift+W | Bring app window to foreground from tray | — |
| 6 | Short Session Start/Stop | Ctrl+Shift+Q | Start or stop a Short Session recording | — |
| 7 | Conflict Warning | Warning Label | Shown in amber next to the affected field when `is_conflict()` returns true. The conflicting hotkey cannot be saved until resolved. | — |
| 8 | Save / Reset | Button Group | **Save Changes**: writes all hotkeys to config; re-registers them via `Hotkeys`. **Reset Defaults**: reverts to factory defaults without confirmation. | — |

---

## Page 9: Speaker Labelling Prompt

Triggered after each recording or voice-profile creation when a new/unidentified speaker is detected.

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Waveform Display | Waveform | Shows amplitude waveform of the captured 10-second audio fragment selected for this speaker. Drawn from the raw PCM buffer. | Read-only | Static once rendered |
| 2 | Start Marker | Draggable Line | Vertical dashed line on waveform indicating the start of the "preview window" (10-second clip to submit to pyannote). Drag to reposition. | `onDrag` → update preview window | Within [0, end_marker - 1s] |
| 3 | End Marker | Draggable Line | End of preview window. | `onDrag` → update preview window | Within [start_marker + 1s, total] |
| 4 | Play Fragment | Button | Plays the audio between start and end markers via python-vlc. | `onClick` → play fragment | `enabled`, `playing` (shows Stop) |
| 5–11 | Metadata Fields | Text Inputs | Last Name *, First Name *, Middle Name, Nickname, Organisation, Position, Note. (* = at least first+last or nickname required.) | `onChange` → validate on blur | Empty or filled |
| 12 | Save Profile | Button | Creates speaker folder (`<last_name>_<first_name>` or nickname or `#001`), writes `speaker.json`, moves captured audio sample to `samples/`, triggers pyannote embedding retraining in background. Enabled only when minimum identifier fields are filled. | `onClick` → validate → write → trigger retrain | `enabled`, `disabled` (validation fails) |
| 13 | Skip | Button | Dismisses the prompt without saving. The speaker is recorded as "Speaker N" in the session. Can be re-identified later via retroactive relabelling. | `onClick` → dismiss | Always enabled |
| 14 | Undo / Redo | Button Pair | Undo/redo for marking actions (assigning speaker to segment, skipping). Independent of all other undo stacks. | `onClick` → revert/re-apply marking decision | — |

---

## Page 10: Session History

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Session Filter | Text Input | Filter sessions by date range or source type. Applies live. | `onInput` → filter list | — |
| 2 | Outdated Indicator | Badge | "⚠ Outdated" shown in amber on sessions where at least one referenced speaker profile has been edited since the session was saved (`output_outdated = true`). | Read-only | `shown`, `hidden` |
| 3 | Selected Session | List Row | Highlighted session. Loads detail in right panel. | `onClick` → load detail | — |
| 4–9 | Detail Fields | Labels | Session ID, Created timestamp, Source Type (`file`/`batch`/`microphone`/`webcam`), Source Path (absolute), Speaker Group, Segment Count. | Read-only | — |
| 10 | Output Files | List | Paths to all `_WSP` files produced by this session. Clicking a path opens the file in the default application. | `onClick path` → `os.startfile()` | — |
| 11 | Regenerate Output | Button | Re-runs output writing using the **current** output content configuration against the stored `segments` array. Does **not** re-run audio processing. New files use `_2`, `_3`, … suffix on collision. | `onClick` → load segments → apply current config → write files | — |
| 12 | Delete Session | Button | Deletes the session JSON file from `<install_dir>/sessions/`. Output files are **not** deleted. Shows confirmation dialog. | `onClick` → confirm → delete JSON | — |

---

## Page 11: Backup and Restore

### Elements

| # | Name | Type | Description | Events | States |
|---|------|------|-------------|--------|--------|
| 1 | Estimated Backup Size | Label | Calculated dynamically: sum of all voice-profile audio samples + config + session JSONs + dictionary file. Updates when the panel opens. | Read-only | — |
| 2 | Backup Destination | File Path + Browse | Destination folder for the ZIP backup file. Defaults to `<install_dir>/backups/`. **Warning** displayed if the path is inside the installation folder (see element 3). | `onChange` → check if inside install dir; show/hide warning | Valid path, inside-install-dir (warning) |
| 3 | Inside-Installation Warning | Warning Box | Shown when Backup Destination is within the installation directory. Text: "Uninstalling the app will delete this backup." The backup can still be created, but the warning remains visible. | Read-only | `visible` (path inside install dir), `hidden` |
| 4 | Create Backup Button | Button | Creates a ZIP archive at the destination: voice-profile library, `config.json`, all session JSONs, dictionary file. File named `SRP_backup_YYYYMMDD_HHMMSS.zip`. | `onClick` → validate path → zip → show success/error | Always enabled (when path valid) |
| 5 | Restore File Picker | File Path + Browse | Path to a previously created backup ZIP. Browse opens a file picker filtered to `.zip`. | `onBrowse` → file picker | Empty → Restore button disabled |
| 6 | Pre-restore Notice | Info Box | Explains that a safety backup will be created automatically before restoring. This safety backup goes to a default temp location and is not configurable. | Read-only | Always visible |
| 7 | Restore Button | Button | Performs restore: (a) creates safety backup, (b) clears current voice-profile library + config + sessions + dictionary, (c) extracts ZIP to installation directory. App restarts after. Shows confirmation dialog before proceeding. | `onClick` → confirm → safety backup → restore → restart | `enabled` (file selected), `disabled` |
| 8 | Irreversibility Warning | Warning Label | Red text: "Current data will be replaced. This cannot be undone." Always visible below the Restore button. | Read-only | Always visible |

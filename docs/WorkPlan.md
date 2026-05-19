# Speech Recognition Program — Detailed Work Plan
**Based on Technical Specification Version 1.0**

---

## How to Use This Document

Each phase contains **tasks** and **checks/tests**. Tasks are labelled `T-XX` and test/check items are labelled `CHK-XX`. Every item references the specification section it satisfies (e.g. `[Spec 3.1]`). The plan is ordered so that each phase produces working, testable output before the next phase begins.

**Test types used throughout:**
- **Unit test (UT)** — automated, isolated function/class test
- **Integration test (IT)** — automated test across two or more modules
- **Manual test (MT)** — step-by-step human verification
- **Regression test (RT)** — re-run of prior tests after a change
- **Performance test (PT)** — timing, throughput, or resource usage
- **Smoke test (ST)** — quick end-to-end pass to confirm nothing is broken

---

## Phase 0 — Project Setup and Research

**Goal:** Establish the development environment, repository, coding conventions, test infrastructure, and design artefacts before any feature code is written.

### Tasks

| ID | Task | Spec ref |
|----|------|----------|
| T-01 | Create private GitHub repository. Add `README.md`, `.gitignore` for Python, and an empty `requirements.txt`. | 1.3.d |
| T-02 | Set up Python virtual environment. Install all preferred libraries. Record exact pinned versions in `requirements.txt`. | 1.3.c, 18 |
| T-03 | Verify CUDA availability: confirm faster-whisper and pyannote.audio detect the RTX 3060 Ti correctly. Document fallback to CPU. | 1.2.b |
| T-04 | Define the project folder structure: `src/`, `tests/`, `platform/`, `languages/`, `assets/sounds/`, `docs/`, `scripts/`. | 17.1 |
| T-05 | Create the platform abstraction layer skeleton. Add `platform/windows/`, `platform/linux/`, `platform/macos/` directories. Implement stub base classes for: installer, auto-start, tray, data-dirs, hotkeys, accelerator, device-enum. Each stub raises `NotImplementedError`. | 17.2 |
| T-06 | Implement the Windows concrete modules (thin wrappers only — no feature logic yet): data directories resolving to `%LOCALAPPDATA%`, device enumeration via pyaudio. | 17.2.a–g |
| T-07 | Design and document the command-line parameter syntax. Write `docs/CLI.md`. Submit for review before implementation. | 15.1.g |
| T-08 | Design the `speaker.json` schema. Write `docs/SPEAKER_JSON_SCHEMA.md` with example. | 4.5.d |
| T-09 | Design the session history JSON schema. Write `docs/SESSION_JSON_SCHEMA.md`. | 11.1 |
| T-10 | Write `docs/BUILD.md` — step-by-step instructions for producing the installer from source. | 15.1.h, 16.4.c |
| T-11 | Produce three UI wireframe options (PDF) covering all nine panels listed in Spec 12.4, plus the session history panel and the Short Session two-field interactive form (Spec 12.6.d). Attach PDF to a dedicated GitHub issue and await written approval before proceeding. A separate wireframe amendment for the two-field form layout must be attached to the same issue and approved before Phase 6-B development begins. | 12.8, 12.6.d |
| T-12 | Set up pytest. Create `tests/` directory with `conftest.py`. Add test audio fixtures: a 10-second clean English WAV, a 10-second clean Finnish WAV, a 30-second two-speaker MP3, a silent WAV, a noisy/bad-quality WAV, and a 1-second WAV (below minimum sample threshold). | — |
| T-13 | Configure a basic CI smoke check in GitHub Actions that runs `pytest tests/unit/` on every push (no model downloads required in CI). | 1.3.d |

### Checks and Tests

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-01 | MT | All libraries install without conflict. `python -c "import whisper, pyannote, customtkinter, pyaudio, cv2, keyboard"` succeeds. | 18 |
| CHK-02 | MT | `faster_whisper` detects CUDA device on the RTX 3060 Ti. CPU fallback produces output when CUDA is disabled. | 1.2.b |
| CHK-03 | MT | All stub modules raise `NotImplementedError` with a descriptive message when called directly. | 17.2 |
| CHK-04 | MT | Wireframe PDF (including Short Session two-field form amendment) reviewed and written approval comment recorded on the GitHub issue before Phase 6-B begins. | 12.8.c, 12.6.d |
| CHK-05 | MT | `requirements.txt` lists every installed library with pinned versions. No library used in code is absent from the file. | 1.3.c |

---

## Phase 1 — Core Audio Pipeline (No GUI)

**Goal:** Implement the complete processing pipeline as a headless library. Every stage is individually testable before the GUI is added.

### 1-A  Audio Ingestion and Extraction

| ID | Task | Spec ref |
|----|------|----------|
| T-14 | Implement `audio.ingest` module. Accepts a file path (MP3, WAV, MP4, AVI) and returns a normalised mono 16 kHz WAV buffer. Uses FFmpeg for MP4/AVI extraction. | 2.1.a |
| T-15 | Implement `audio.device` module (Windows concrete class). Enumerates microphone and webcam audio devices via pyaudio. Returns a list of `DeviceInfo` objects with id, name, and type. | 2.2.a |
| T-16 | Implement `audio.capture` module. Opens a pyaudio stream for a given device, records until stopped, returns a WAV buffer. | 2.1.b–c |
| T-17 | Implement stream splitting logic: monitor duration, write to a new buffer at the 5-hour boundary without resetting speaker numbering. | 2.3.a–d |

**Checks and Tests — 1-A**

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-06 | UT | `audio.ingest` correctly loads MP3, WAV, MP4, AVI. Output is always mono, 16 kHz, float32. | 2.1.a |
| CHK-07 | UT | MP4 and AVI ingestion extracts audio only; no video data in output buffer. | 2.1.a |
| CHK-08 | UT | Passing a non-existent file path raises `FileNotFoundError` with a clear message. | — |
| CHK-09 | UT | Passing an unsupported format (e.g. `.ogg`) raises a descriptive `ValueError`. | 2.1.a |
| CHK-10 | MT | `audio.device.list_devices()` returns at least the system default microphone on the test machine. | 2.2.a |
| CHK-11 | MT | Partial-name device matching: `--input-device "Realtek"` matches "Microphone (Realtek Audio HD)". | 2.2.d |
| CHK-12 | MT | No-match case: `--input-device "ZZZNOMATCH"` prints an error listing all available devices, exits non-zero. | 2.2.d |
| CHK-13 | IT | Record 5 seconds from the microphone; verify the returned buffer is non-silent and has the correct sample rate. | 2.1.b |
| CHK-14 | UT | Stream splitting logic: a synthetic 5-hour-and-1-minute buffer triggers a split at exactly 5 hours. Output buffers 1 and 2 have correct durations. | 2.3.a–b |

### 1-B  Speaker Diarization

| ID | Task | Spec ref |
|----|------|----------|
| T-18 | Implement `diarization.engine` module. Wraps pyannote.audio. Accepts a WAV buffer, returns a list of `Segment(start, end, speaker_id)` objects. | 4.1.a |
| T-19 | Implement HuggingFace licence check. On module load, check a persistent `licence_accepted` flag in the config file. If absent or false, return a `LicenceNotAcceptedError` and set all diarization outputs to Unknown. | 4.7.a–b |
| T-20 | Implement speaker numbering: assign Speaker 1, Speaker 2, etc. to segments whose `speaker_id` is not in the active library group. Reset numbering at session/batch start. | 4.2.a–b |
| T-21 | Implement short-segment confidence flagging: segments shorter than 10 seconds receive a low confidence marker. | 4.1.c |

**Checks and Tests — 1-B**

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-15 | UT | `LicenceNotAcceptedError` is raised when `licence_accepted = false`. All returned segments have `speaker_id = "Unknown"`. | 4.7.b |
| CHK-16 | IT | Two-speaker 30-second MP3 fixture produces at least 2 distinct speaker IDs from pyannote.audio. | 4.1.a |
| CHK-17 | UT | Speaker numbering resets to 1 at the start of a new session object. | 4.2.b |
| CHK-18 | UT | A segment of 8 seconds is flagged `low_confidence = True`. A segment of 12 seconds is not. | 4.1.c |
| CHK-19 | PT | Diarization of a 60-second WAV completes in under 120 seconds on CPU (no CUDA). Record result for baseline. | — |
| CHK-20 | PT | Diarization of a 60-second WAV on the RTX 3060 Ti completes in under 30 seconds. Record result. | 1.2.b |

### 1-C  Speech-to-Text

| ID | Task | Spec ref |
|----|------|----------|
| T-22 | Implement `transcription.engine` module. Wraps faster-whisper. Accepts a WAV buffer and a list of `Segment` objects, transcribes each segment, returns `TranscribedSegment(speaker_id, start, end, text, language, confidence, no_speech_prob)`. | 3.1.a, 3.5.2 |
| T-23 | Implement language detection output: attach detected language name to each segment. | 3.3.a |
| T-24 | Implement bad audio detection: if `no_speech_prob > 0.6`, mark the segment as bad and replace unrecognised tokens with `XXXXX`. | 3.4.a–b |
| T-25 | Implement model checksum verification on startup: compute SHA-256 of model files, compare to stored checksum, trigger retraining flag if mismatch. | 3.2.d |

**Checks and Tests — 1-C**

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-21 | UT | English WAV fixture transcribes to expected text (reference string check, ≥90% word accuracy). | 3.1 |
| CHK-22 | UT | Finnish WAV fixture transcribes correctly; detected language is `"Finnish"`. | 3.3.a |
| CHK-23 | UT | Silent WAV fixture: `no_speech_prob > 0.6`; output text contains only `XXXXX`. | 3.4.a–b |
| CHK-24 | UT | Noisy WAV fixture triggers bad audio marker; bad-audio flag is `True`. | 3.4.a |
| CHK-25 | IT | Full pipeline: two-speaker MP3 → diarization → transcription → each segment has correct `speaker_id`, non-empty `text`, and a `confidence` value between 0 and 1. | 3.5.1–2 |
| CHK-26 | UT | Checksum mismatch (simulate by writing a corrupted checksum file) raises a retraining-required flag. Matching checksum clears the flag. | 3.2.d |
| CHK-27 | PT | Transcription of a 60-second English WAV on CPU completes in under 180 seconds. Record result. | — |
| CHK-28 | PT | Transcription of a 60-second English WAV on CUDA completes in under 30 seconds. Record result. | 1.2.b |

### 1-D  Substitution Dictionary

| ID | Task | Spec ref |
|----|------|----------|
| T-26 | Implement `dictionary.store` module: load/save dictionary as a structured JSON file within the installation folder. | 7.1 |
| T-27 | Implement `dictionary.matcher`: apply substitutions to a list of transcribed segments. Case-insensitive whole-word matching. Support fnmatch wildcards (`*`, `?`). | 7.2.a–c |
| T-28 | Implement `dictionary.importer`: parse a CSV file, add new entries, reject conflicts, return an `ImportResult` summary object. | 7.3.d |
| T-29 | Implement `dictionary.exporter`: write current dictionary to a CSV file. | 7.3.c |

**Checks and Tests — 1-D**

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-29 | UT | `"Hello"` matches dictionary key `"hello"` (case-insensitive). | 7.2.a |
| CHK-30 | UT | `"Helloing"` does NOT match whole-word key `"hello"`. | 7.2.b |
| CHK-31 | UT | Wildcard `"hel*"` matches `"hello"`, `"help"`, `"helpdesk"`. | 7.2.c |
| CHK-32 | UT | Wildcard `"h?llo"` matches `"hello"` but not `"hllo"`. | 7.2.c |
| CHK-33 | UT | Import CSV with 10 entries: 6 new + 4 conflicts. `ImportResult` shows 6 added, 4 rejected, lists all 4 rejected source words. | 7.3.d |
| CHK-34 | UT | Export → re-import round-trip: output CSV re-imports without conflicts and produces an identical dictionary. | 7.3.c |
| CHK-35 | UT | Dictionary application does not alter speaker confidence scores. | 7.2.e |
| CHK-36 | UT | Dictionary is NOT applied when called from the retraining code path. | 7.1 |

### 1-E  Translation

| ID | Task | Spec ref |
|----|------|----------|
| T-30 | Implement `translation.opus_mt` module: load Helsinki-NLP OPUS-MT model for a given language pair on demand, translate a list of strings. Download model files if absent (with progress callback). | 6.3.a |
| T-31 | Implement `translation.google` module: call the free Google Translate endpoint, return translated strings. Raise `TranslationServiceError` on HTTP failure or timeout. | 6.3.b |
| T-32 | Implement `translation.engine`: dispatcher that routes to the active engine. Applies translation only after the substitution dictionary has been applied. | 6.1.a, 3.5.5 |
| T-33 | Implement OPUS-MT quality warning: when a language pair is known to have limited coverage (Chinese pairs), attach a `quality_warning = True` flag to the returned `LanguagePairInfo` object. | 6.3.a |

**Checks and Tests — 1-E**

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-37 | UT | OPUS-MT translates English → Finnish. Output is non-empty and structurally correct. | 6.3.a |
| CHK-38 | UT | `TranslationServiceError` is raised when the Google endpoint is mocked to return HTTP 429. Error propagates without falling back to OPUS-MT. | 6.3.b |
| CHK-39 | UT | Translation is only called after substitution: a substituted word appears in the translation input, not the original word. | 6.1.a |
| CHK-40 | UT | `LanguagePairInfo` for English→Chinese Simplified has `quality_warning = True`. English→Finnish has `quality_warning = False`. | 6.3.a |
| CHK-41 | UT | When translation is disabled, the engine returns the input text unchanged. | 6.1.b |
| CHK-42 | IT | Full pipeline with translation: English WAV → transcription → dictionary → OPUS-MT Finnish translation → output contains Finnish text. | 3.5 |

### 1-F  Output Writers

| ID | Task | Spec ref |
|----|------|----------|
| T-34 | Implement `output.txt_writer`: writes segment blocks to a `.txt` file. Each field on its own line; segments separated by blank lines. | 8.4.c |
| T-35 | Implement `output.docx_writer`: writes segment blocks to a `.docx` file using python-docx. Each segment is a distinct paragraph. | 8.4.c |
| T-36 | Implement `output.srt_writer`: writes SRT file. Always includes timestamp (HH:MM:SS,mmm), speaker name (if available), and speech text. Suppresses language prefix. | 8.4.d |
| T-37 | Implement `output.json_writer`: writes all six fields for every segment regardless of field selection. | 8.4.e |
| T-38 | Implement `output.clipboard_writer`: copies text to the Windows clipboard via `pyperclip` or `ctypes`. Raises `ClipboardNotAvailableError` for non-microphone input. | 8.1.c |
| T-39 | Implement `output.naming`: generate output file names following the `_WSP` convention, numeric suffix collision avoidance, and `_part1/_part2` for split streams. | 8.3.a–c |
| T-40 | Implement `output.field_selector`: apply the active output content configuration to a list of `TranscribedSegment` objects before passing to the writers. | 8.4.a–b |

**Checks and Tests — 1-F**

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-43 | UT | TXT writer: 3-segment input with all 6 fields enabled produces correct file content — field order, blank-line separators verified. | 8.4.c |
| CHK-44 | UT | TXT writer: Language field disabled → no language prefix in output. | 3.3.c |
| CHK-45 | UT | SRT writer: output is valid SRT (parseable by a third-party SRT parser). Timestamps match segment start times. Speaker name appears in subtitle text. Language prefix absent. | 8.4.d |
| CHK-46 | UT | JSON writer: output is valid JSON. All 6 fields present for every segment regardless of field selection. | 8.4.e |
| CHK-47 | UT | DOCX writer: output opens without error in python-docx. Segment count matches input. | 8.4.c |
| CHK-48 | UT | `output.naming`: `interview.mp3` → `interview_WSP.txt`. Second run with existing file → `interview_WSP_2.txt`. Third → `interview_WSP_3.txt`. | 8.3.b |
| CHK-49 | UT | `output.naming` for split streams: part 1 → `interview_WSP_part1.txt`, part 2 → `interview_WSP_part2.txt`. | 8.3.c |
| CHK-50 | UT | Clipboard writer raises `ClipboardNotAvailableError` when `source_type = "file"`. | 8.1.c |
| CHK-51 | IT | Full pipeline to all four file formats simultaneously: all four files exist, are non-empty, and pass format validation. | 8.1.b |

---

## Phase 2 — Voice Profile Library

**Goal:** Implement all voice library storage, management, and retraining logic.

### Tasks

| ID | Task | Spec ref |
|----|------|----------|
| T-41 | Implement `library.storage` module: create/read/update/delete speaker subfolders, read/write `speaker.json`, manage sequential sample naming (`sample_001.mp3`, etc.). | 4.5.a–d |
| T-42 | Implement folder name generation: join last/first/middle/nickname with underscores, replace invalid Windows chars, append numeric ID for all-empty-name profiles. | 4.5.a–b |
| T-43 | Implement `library.profile_creator`: extract 10-second segment from any supported audio format (via FFmpeg), generate pyannote embedding, save sample and vector, record model checksum in `speaker.json`. | 5.2.a |
| T-44 | Implement short-sample warning in `library.profile_creator`: if audio < 10 seconds, set `low_confidence = True` flag and proceed. | 5.3 |
| T-45 | Implement conflict resolution: `overwrite`, `merge` (add new sample as next sequential file), `reject`. | 5.4.a–c |
| T-46 | Implement `library.retrainer`: reprocess all `sample_NNN.mp3` files for every speaker, average embeddings, update `speaker.json` checksum and sample count, provide progress callback, produce a `RetrainingResult` summary. | 4.6.a–d |
| T-47 | Implement revert-model option: re-download the previous model version (URL from `speaker.json` checksum record), run retraining on the old model. | 4.6.e |
| T-48 | Implement `library.groups`: create, rename, delete groups; add/remove speakers; persist group membership in `speaker.json`; ensure deleting a profile removes it from all groups; ensure renaming updates all group membership references. | 4.4.d–e |
| T-49 | Implement `library.exporter`: produce a ZIP archive of selected speaker subfolders. | 5.5.a |
| T-50 | Implement `library.importer`: unpack a ZIP archive, resolve conflicts via the conflict resolver, create missing groups, trigger retraining prompt flag. | 5.5.b–c |

### Checks and Tests — Phase 2

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-52 | UT | Folder name `Smith_John__` is generated for last=Smith, first=John, middle=empty, nickname=empty. | 4.5.a |
| CHK-53 | UT | All-empty name fields produce `____001`; nickname field in JSON = `"#001"`. | 4.5.b |
| CHK-54 | UT | Invalid Windows chars (`/`, `:`, `"`) in name fields are replaced with `_` in folder name but preserved in `speaker.json`. | 4.5.a |
| CHK-55 | UT | Profile created from the 10-second English WAV fixture: subfolder exists, `sample_001.mp3` exists, vector file exists, `speaker.json` is valid and contains correct checksum. | 5.2.a |
| CHK-56 | UT | Profile created from the 1-second WAV fixture: `low_confidence = True` in JSON; subfolder and files still created. | 5.3 |
| CHK-57 | UT | Conflict — overwrite: existing `sample_001.mp3` is replaced; vector file is replaced; sample list in JSON is reset. | 5.4.a |
| CHK-58 | UT | Conflict — merge: new sample saved as `sample_002.mp3`; original `sample_001.mp3` unchanged; JSON sample list has both entries. | 5.4.b |
| CHK-59 | UT | Conflict — reject: folder is unchanged after the operation. | 5.4.c |
| CHK-60 | IT | Retraining: create 3 profiles, simulate a model update (write new checksum), run `library.retrainer`. All 3 profiles have updated checksums; `RetrainingResult` shows 3 retrained, 0 failed. | 4.6.a–d |
| CHK-61 | UT | Retraining summary correctly reports a profile with a missing MP3 file as failed. | 4.6.d |
| CHK-62 | UT | `library.groups.delete_group()` removes the group; member profiles no longer list it in their `speaker.json` groups array. | 4.4.d |
| CHK-63 | UT | `library.storage.delete_profile()` removes the speaker from every group that referenced them. | 4.4.e |
| CHK-64 | UT | `library.storage.rename_profile()` updates group membership references in all groups. | 4.4.e |
| CHK-65 | IT | Export 2 profiles → ZIP. Delete both profiles. Import ZIP. Both profiles restored with correct metadata, samples, and group membership. | 5.5.a–b |
| CHK-66 | UT | Import triggers the retraining-required flag after completion. | 5.5.c |
| CHK-67 | UT | Imported profile belonging to a group that does not exist on the target: group is created automatically. | 5.5.b |

---

## Phase 3 — Session Management and History

**Goal:** Implement session lifecycle, post-session labelling, and the session history subsystem.

### Tasks

| ID | Task | Spec ref |
|----|------|----------|
| T-51 | Implement `session.manager`: manages a single processing session. Holds the list of `TranscribedSegment` objects, speaker mappings, and session metadata. | 4.2, 4.3 |
| T-52 | Implement post-session retroactive relabelling: once a Speaker N is confirmed as a named person, replace all instances of that speaker ID across the session's segment list. | 4.3.d |
| T-53 | Implement `session.history`: save completed sessions as JSON files in the `sessions/` subfolder. Load session list. Delete individual sessions. | 11.1.a–c |
| T-54 | Implement output regeneration: load a session JSON, apply the current output content configuration, write new output files with collision-safe naming. | 11.2.a–c |
| T-55 | Implement outdated-output detection: when a speaker profile is edited, scan all session JSON files for segments referencing that speaker and set `output_outdated = true`. | 11.3.a |
| T-56 | Implement `session.history` CLI commands: `--list-sessions` (tabular print), `--regenerate-output`. | 11.4 |

### Checks and Tests — Phase 3

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-68 | UT | Retroactive relabelling: session with 5 segments for Speaker 1 — after confirming name "Alice", all 5 segments have `speaker_name = "Alice"`. | 4.3.d |
| CHK-69 | UT | Skipped speaker retains `"Speaker 1"` label in the saved session JSON. | 4.3.c |
| CHK-70 | UT | Session saved to `sessions/` folder. Reloading the JSON produces an identical segment list. | 11.1.a |
| CHK-71 | UT | Output regeneration produces a new output file. Content reflects the current (modified) output content configuration, not the original. | 11.2.b |
| CHK-72 | UT | Regenerated file naming: if `interview_WSP.txt` exists, regeneration produces `interview_WSP_2.txt`. | 11.2.c |
| CHK-73 | UT | After editing a speaker profile name, the session history entry for that speaker has `output_outdated = true`. | 11.3.a |
| CHK-74 | IT | `--list-sessions` CLI command prints a table with at least session ID and date for each stored session. Exit code 0. | 11.4 |
| CHK-75 | IT | `--regenerate-output` CLI command produces an output file and exits with code 0. | 11.4 |

---

## Phase 4 — Configuration, Settings, and Backup

**Goal:** Implement the persistent configuration system, application settings, backup/restore, and the substitution dictionary persistence layer.

### Tasks

| ID | Task | Spec ref |
|----|------|----------|
| T-57 | Implement `config.store` module: read/write a JSON configuration file in the installation folder. Define all configurable keys with defaults. | 1.2 (general) |
| T-58 | Implement output folder configuration: default to installation folder, user-overridable, persisted in config. | 8.2.a–b |
| T-59 | Implement output content configuration: persist field selection (6 toggles) and full-name format in config. | 8.4.a |
| T-60 | Implement hotkey configuration: store key bindings in config with defaults (Ctrl+Shift+R/S/C). Detect conflicts with common Windows shortcuts; return a `ConflictWarning` if found. | 12.5.a–d |
| T-61 | Implement translation engine selection: persist chosen engine (OPUS-MT / Google Translate) in config. | 6.3.c |
| T-62 | Implement recording mode persistence: save last-used mode (Regular / Short Session). Restore on startup. | 12.6.c |
| T-63 | Implement UI language selection: persist selected language code in config; default to `"en"` on first launch. | 12.1.b |
| T-64 | Implement `backup.manager`: create ZIP archive of all user data (config, dictionary, voice library, groups, output config, session history). Display estimated size before creating. Warn if backup path is inside the installation folder. | 14.1, 14.2 |
| T-65 | Implement `backup.restorer`: create a safety backup of current state, then unpack the archive over all user data after confirmation. | 14.3 |
| T-66 | Implement CLI backup/restore commands: `--backup "<path>"`, `--restore "<path>"`. Safety backup location printed to stdout in CLI mode. | 14.2.d, 14.3.c |

### Checks and Tests — Phase 4

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-76 | UT | Config file is created with correct defaults on first run. Reloading returns identical values. | T-57 |
| CHK-77 | UT | Hotkey conflict check: `Ctrl+C` returns `ConflictWarning`. `Ctrl+Shift+R` (not a standard Windows shortcut) returns no warning. | 12.5.d |
| CHK-78 | UT | Recording mode saved as `"short"` on shutdown; restored as `"short"` on next startup. | 12.6.c |
| CHK-79 | UT | UI language defaults to `"en"` on a fresh config file. | 12.1.b |
| CHK-80 | UT | Backup creates a valid ZIP. Re-extracting the ZIP produces the correct folder structure with all expected files. | 14.1 |
| CHK-81 | UT | Estimated backup size displayed before creation is within 10% of the actual archive size. | 14.2.a |
| CHK-82 | UT | Backup path inside installation folder triggers a warning flag in the returned result. | 14.2.b |
| CHK-83 | IT | Restore: modify config, dictionary, and a profile. Run restore from a previously created backup. Verify all three revert to backup state. Safety backup file exists at the printed path. | 14.3.a–b |
| CHK-84 | IT | `--backup` CLI command produces a ZIP and exits with code 0. | 14.2.d |
| CHK-85 | IT | `--restore` CLI command prints safety backup location to stdout before restoring, exits with code 0. | 14.3.c |

---

## Phase 5 — Command-Line Interface

**Goal:** Implement the full CLI front-end as a thin layer on top of the pipeline and library modules.

### Tasks

| ID | Task | Spec ref |
|----|------|----------|
| T-67 | Implement `cli.parser`: parse all CLI parameters using `argparse`. Validate parameter names; exit with a specific error message for unrecognised parameters. | 15.1.c |
| T-68 | Implement defaults from last session config for all optional parameters. Validate mandatory `--input` files. | 15.1.d–e |
| T-69 | Implement `--help`: print parameter list with descriptions and examples. Exit code 0. | 15.1.f |
| T-70 | Implement CLI batch processing: call audio ingestion, diarization, transcription, substitution, translation, and output in sequence for each input file. | 15.2.a |
| T-71 | Implement CLI profile management commands: `--profile-create`, `--profile-delete`, `--profile-rename`. | 15.2.b |
| T-72 | Implement CLI dictionary commands: `--dict-export`, `--dict-import`. Print import summary to stdout. | 15.2.c |
| T-73 | Suppress completion sound, tray notification, and GUI in CLI mode. Return exit code 0 on success, non-zero on any error. | 12.7.c, 13.2.c, 15.1.a |
| T-74 | Implement HuggingFace licence warning in CLI mode: print warning to stdout and continue with Unknown labels. | 4.7.e |
| T-75 | Ensure all CLI output (errors, warnings, summaries) is always in English. | 15.1.b |

### Checks and Tests — Phase 5

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-86 | IT | `wsp.exe --input audio.mp3` processes the file and writes output to the configured output folder. Exit code 0. | 15.2.a |
| CHK-87 | IT | `wsp.exe --input audio.mp3 --output-format txt json` produces both a `.txt` and a `.json` file. | 15.2.a |
| CHK-88 | UT | `wsp.exe --unknownparam` prints a specific error identifying `--unknownparam` as unrecognised. Exit code non-zero. | 15.1.c |
| CHK-89 | UT | `wsp.exe` (no arguments, no saved config) prints a "missing input files" error. Exit code non-zero. | 15.1.e |
| CHK-90 | IT | `wsp.exe --help` prints at least 10 parameter names with descriptions. Exit code 0. No GUI opens. | 15.1.f |
| CHK-91 | IT | `wsp.exe --profile-create --lastname Smith --firstname John --audio sample.mp3` creates a profile in the library. | 15.2.b |
| CHK-92 | IT | `wsp.exe --profile-delete --name "Smith_John__"` removes the profile from the library. | 15.2.b |
| CHK-93 | IT | `wsp.exe --dict-import dict.csv` prints correct summary (added/rejected counts and rejected words). | 15.2.c |
| CHK-94 | MT | Run CLI batch on a 2-minute audio file with licence NOT accepted. Output contains "Unknown" speaker labels. Warning printed to stdout. Exit code 0. | 4.7.e |
| CHK-95 | MT | All CLI output messages are in English even when UI language is set to Finnish in config. | 15.1.b |

---

## Phase 6 — Graphical User Interface

**Goal:** Build the GUI on top of the approved wireframe design using CustomTkinter. All business logic is already implemented; the GUI connects controls to the pipeline.

### 6-A  Application Shell and Navigation

| ID | Task | Spec ref |
|----|------|----------|
| T-76 | Implement the main application window shell following the approved wireframe design. Implement panel navigation (Settings, Voice Profile Management, Substitution Dictionary, Batch Queue, Output Config, Hotkeys, Speaker Labelling, Session History, Backup/Restore). | 12.3–12.4 |
| T-77 | Implement UI language loading from JSON files. Apply translations to all controls at startup and on language change. Implement language file restore from backup on corruption. | 12.1.b–d |
| T-78 | Implement the recording mode toggle (Regular / Short Session) in the main window. | 12.6.c |
| T-79 | Implement the recording indicator: pulsing red dot during recording, grey when idle. | 12.2.a |
| T-80 | Implement the two progress bars: file-level and queue-level (queue bar hidden outside batch processing). | 12.2.b–c |
| T-81 | Implement the input device dropdown in the main window. Wire to `audio.device` module. | 2.2.a |
| T-82 | Implement the real-time signal level meter in the main window and in the settings panel. | 2.2.c |
| T-83 | Implement the main window text display area as a switchable layout: single output text area in Regular mode; two-field interactive form in Short Session mode when the window is visible. The layout switches dynamically when the recording mode toggle changes. | 12.3, 12.6.d |

### 6-B  Recording and Processing Controls

| ID | Task | Spec ref |
|----|------|----------|
| T-84 | Implement Regular mode recording: start/stop via hotkey or UI button. Run full pipeline in a background thread. Update output display on completion. | 12.6.a |
| T-85 | Implement Short Session mode pipeline: start/stop via hotkey, run pipeline in background thread, auto-copy to clipboard, play completion sound. When window is visible, populate the two-field form after the beep (step 9). When minimised to tray, operate silently ("run once and forget"). | 12.6.b–d |
| T-86 | Implement global hotkey registration via the keyboard library. Apply defaults if first-launch setup is skipped. | 12.5.a–c |
| T-87 | Implement audio playback in the main window: seek slider, click-on-timestamp, python-vlc backend. Disable playback during recording. | 10.1 |
| T-88 | Implement completion sound: load sound file, play on any processing completion event. Configurable; suppressed in CLI mode. | 12.7 |
| T-127 | Implement the two-field interactive form layout within the main window for Short Session mode. First field: editable, with a button whose label switches dynamically between "Translate and save to clipboard" (translation enabled) and "Copy to clipboard" (translation disabled). Second field: editable, with a "Save to clipboard" button. Both fields use OS-level text undo/redo independently. | 12.6.d |
| T-128 | Implement dynamic layout change when the translation setting changes: hide the second field and its button, expand the first field to fill the space. Reverse when translation is re-enabled. Update the first button label at the same time. | 12.6.d |
| T-129 | Implement field clearing at the start of each new Short Session recording: both fields are cleared when the start hotkey is pressed. | 12.6.d |
| T-130 | Implement the "Translate and save to clipboard" button action: translate the current content of the first field, overwrite the second field with the result, write the result to the clipboard. When translation is disabled (button shows "Copy to clipboard"): copy the first field's current content to the clipboard directly. Always overwrites the second field regardless of its current content. | 12.6.d |
| T-131 | Implement the "Save to clipboard" button action: copy the current content of the second field to the clipboard. | 12.6.d |
| T-132 | Implement session history update on each clipboard write: the single session record for the current recording is updated with the most recently copied text each time the clipboard is written (automatic write + up to two button-triggered writes). | 11.1, 12.6.d |
| T-133 | Implement minimised-state branching for Short Session mode: if the window is minimised to the tray when the start hotkey is pressed, the pipeline runs silently without showing the two-field form. The form is shown when the window is restored if it is the most recent session. | 12.6.d |

### 6-C  Settings Panel

| ID | Task | Spec ref |
|----|------|----------|
| T-89 | Implement the Settings panel: input device selection, signal level meter, UI language picker, translation engine selector with OPUS-MT quality warnings, hotkey display, completion sound config, tray and auto-start toggles. | 2.2, 6.3, 12.1, 12.5, 12.7, 13 |
| T-90 | Implement HuggingFace licence acceptance in settings: display licence text, write `licence_accepted = true` to config, prompt user to restart. | 4.7.c |
| T-91 | Implement Whisper model change: present model options, download new model on change, update stored checksum. | 3.2.c |

### 6-D  Voice Profile Management Panel

| ID | Task | Spec ref |
|----|------|----------|
| T-92 | Implement the Voice Profile Management panel: two-section layout (speaker list + group list), drag-to-group, add/remove buttons. | 5.1 |
| T-93 | Implement the Create Profile dialog: file picker, python-vlc playback, draggable 10-second start marker, preview button, metadata entry form (all fields). | 5.2.a |
| T-94 | Implement the Edit Profile dialog: load all fields from `speaker.json`, save on confirm, update folder name and group references. | 5.2.b |
| T-95 | Implement bulk delete with confirmation dialog. | 5.2.c |
| T-96 | Implement the conflict resolution dialog (overwrite / merge / reject) for both manual create and import. | 5.4 |
| T-97 | Implement profile import/export: file picker for ZIP, progress indicator, trigger retraining prompt after import. | 5.5 |
| T-98 | Implement the full name output format configurator in settings: component selector, order drag-and-drop, live preview. | 5.6 |
| T-99 | Implement group management: create/rename/delete groups from the group list panel. | 4.4.d |
| T-100 | Implement speaker group selector in the main window (active group dropdown). | 4.4.a–b |

### 6-E  Other Panels

| ID | Task | Spec ref |
|----|------|----------|
| T-101 | Implement the Substitution Dictionary panel: table view (source / replacement columns), add/edit/delete row, undo/redo per the dictionary's own history, CSV import/export buttons. | 7.3.a–b |
| T-102 | Implement the Batch Queue panel: file list with add/remove, start button, FIFO locking during run, error pop-up at end. | 9.1–9.2 |
| T-103 | Implement the Output Content Configuration panel: 6 field toggles, format checkboxes (TXT/DOCX/SRT/JSON/display/clipboard), output folder picker. | 8.1–8.4 |
| T-104 | Implement the Hotkey Configuration panel: key capture control per action, conflict warning display, save. | 12.5 |
| T-105 | Implement the Speaker Labelling Prompt panel: audio playback of captured fragment, metadata form (last/first/middle/nickname/org/position/note), Skip button, undo/redo for marking actions. | 4.3, 19 (undo/redo) |
| T-106 | Implement the Session History panel: session list, delete, regenerate output button, "output outdated" indicator. | 11 |
| T-107 | Implement the Backup and Restore panel: backup button with size estimate, restore button with pre-restore safety backup, backup folder selector with inside-installation-folder warning. | 14 |

### 6-F  System Tray

| ID | Task | Spec ref |
|----|------|----------|
| T-108 | Implement system tray icon, right-click context menu (Open, mode indicator, Start/Stop with greying logic, Exit). | 13.1 |
| T-109 | Implement Exit-during-processing confirmation dialog from tray. | 13.1.d |
| T-110 | Implement tray balloon notification on processing completion (independent of completion sound). | 13.2 |
| T-111 | Implement "Minimize to tray" behaviour: intercept window minimize, hide from taskbar. | 13.1.a |
| T-112 | Implement auto-start toggle: write/remove HKCU registry entry via Windows platform module. | 13.3 |

### Checks and Tests — Phase 6

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-96 | MT | Main window opens. All nine panel navigation links work. Language defaults to English. | 12.3–12.4 |
| CHK-97 | MT | Change UI language to Finnish. All control labels change to Finnish immediately. Change back to English; labels revert. | 12.1.b |
| CHK-98 | MT | Delete a language JSON file. Application shows an error message and restores it from backup. Application starts successfully afterwards. | 12.1.d |
| CHK-99 | MT | Recording indicator pulses red during microphone recording, turns grey on stop. | 12.2.a |
| CHK-100 | MT | File-level progress bar advances during single-file processing. Queue-level bar is hidden outside batch mode, visible during batch. | 12.2.b–c |
| CHK-101 | MT | Record a short sentence (Regular mode). Output appears in the display area. Output file written to the configured folder. | 12.6.a |
| CHK-102 | MT | Short Session mode (window visible): press start hotkey, speak, press stop hotkey. Pipeline runs. Both text fields are populated. First field contains untranslated text, second field contains translated text. Clipboard holds the translated text. Completion sound plays. | 12.6.b–d |
| CHK-163 | MT | Short Session mode (window visible, translation enabled): both fields populated after processing. Verify first field = raw transcription, second field = translated text. | 12.6.d |
| CHK-164 | MT | Disable translation in settings. Second field and "Save to clipboard" button disappear. First field expands. First button label changes to "Copy to clipboard". | 12.6.d |
| CHK-165 | MT | Re-enable translation. Second field and button reappear. First button label reverts to "Translate and save to clipboard". First field contracts. | 12.6.d |
| CHK-166 | MT | Edit the first field, click "Translate and save to clipboard". Second field is overwritten with a fresh translation of the edited text. Clipboard contains the new translation. | 12.6.d |
| CHK-167 | MT | Edit the second field, click "Save to clipboard". Clipboard contains the edited translated text, not the automatically generated translation. | 12.6.d |
| CHK-168 | MT | Translation disabled: edit the first field, click "Copy to clipboard". Clipboard contains the edited untranslated text. | 12.6.d |
| CHK-169 | MT | Press the start hotkey for a new Short Session recording. Both fields are cleared immediately before recording begins, regardless of previous content. | 12.6.d |
| CHK-170 | MT | Take no action after processing. Press start hotkey for a second recording. Both fields are cleared. Previous content is gone. | 12.6.d |
| CHK-171 | MT | Verify three clipboard writes in one session: (1) automatic after pipeline; (2) after "Translate and save to clipboard" with edited text; (3) after "Save to clipboard" with further edited text. Each write produces the correct distinct content. | 12.6.d |
| CHK-172 | MT | Session history contains exactly one record per recording. After three clipboard writes, the record reflects the third (most recent) clipboard content. | 11.1, 12.6.d |
| CHK-173 | MT | Minimise window to tray. Press start hotkey. Recording runs, pipeline completes silently. Clipboard receives result. Beep plays. No form is shown. Restore window — fields show the result from the silent run. | 12.6.d |
| CHK-174 | MT | OS-level undo (Ctrl+Z) within the first field reverts the last text edit without affecting speaker marking or dictionary undo histories. | 12.6.d |
| CHK-175 | MT | OS-level undo (Ctrl+Z) within the second field reverts the last text edit independently of the first field's undo history. | 12.6.d |
| CHK-176 | RT | Re-run CHK-101 (Regular mode output area) after implementing the two-field form. Verify the single output text display area still works correctly in Regular mode and is unaffected by the Short Session form. | 12.6.a–d |
| CHK-103 | MT | Drag the seek slider; playback jumps. Click a timestamp in the output text; playback jumps to that position. Both work simultaneously. | 10.1.b–c |
| CHK-104 | MT | Playback controls are disabled (greyed out) during active recording. Re-enabled after recording stops. | 10.1.d |
| CHK-105 | MT | Create a speaker profile: provide the 30-second MP3 fixture, set start marker at 5 seconds, click Preview (plays the selected 10-second window), click Confirm. Profile appears in the speaker list. | 5.2.a |
| CHK-106 | MT | Edit a speaker profile: change the last name. Speaker list and all group membership labels update immediately. | 5.2.b |
| CHK-107 | MT | Delete two profiles simultaneously (bulk delete). Both subfolders are removed. Both are removed from any groups they belonged to. | 5.2.c |
| CHK-108 | MT | Import a ZIP with 3 profiles including 1 conflict. Conflict dialog appears. Choose Merge. Library contains original + merged sample. Retraining prompt appears after import. | 5.5.b, 4.6 |
| CHK-109 | MT | Substitution dictionary: add a row, delete a row, edit a row. Ctrl+Z undoes the last dictionary action without undoing any speaker marking action. | 7.3.a–b |
| CHK-110 | MT | Batch queue: add 3 files. Start processing. Queue is locked (add/remove disabled). After processing, pop-up lists any failed files. | 9.1–9.2 |
| CHK-111 | MT | Output configuration: enable only TXT and JSON. Process a file. Only `.txt` and `.json` files are created; no `.docx` or `.srt`. | 8.1.b |
| CHK-112 | MT | Set clipboard as the only output destination with a file as input. Informational message appears explaining clipboard is unavailable for file input. | 8.1.c |
| CHK-113 | MT | Assign `Ctrl+C` as a hotkey. Conflict warning appears. Proceed anyway. Hotkey is saved. | 12.5.d |
| CHK-114 | MT | Speaker labelling prompt: play audio fragment, enter name, click Skip on the second speaker. Output text shows first speaker's name and "Speaker 2". | 4.3.b–c |
| CHK-115 | MT | Speaker marking undo: label a speaker incorrectly, press Ctrl+Z in the labelling prompt. Label reverts. | 19 (undo/redo) |
| CHK-116 | MT | Session History panel: find a previous session, click Regenerate Output. New output file appears in the output folder. | 11.2 |
| CHK-117 | MT | Edit a speaker's organisation in the profile editor. Session history entry for that speaker shows "output outdated" indicator. | 11.3.a |
| CHK-118 | MT | Tray icon right-click: Start recording is greyed out during recording; Stop recording is greyed out when idle. | 13.1.b |
| CHK-119 | MT | Click Exit from tray while batch is running. Confirmation dialog appears. Click Cancel — processing continues. Click Exit again, confirm — application exits and batch stops. | 13.1.d |
| CHK-120 | MT | Enable "Minimize to tray". Minimize window — disappears from taskbar, tray icon visible. Double-click tray icon — window restores. | 13.1.a |
| CHK-121 | MT | Enable "Auto-start with Windows". Verify HKCU registry key `Software\Microsoft\Windows\CurrentVersion\Run` contains the application entry. Disable it — key is removed. | 13.3 |
| CHK-122 | MT | Tray completion notification appears after batch processing ends (separate from the completion sound). Disable tray notifications in settings — notification no longer appears. | 13.2 |

---

## Phase 7 — Installer

**Goal:** Package the application into a distributable Windows installer.

### Tasks

| ID | Task | Spec ref |
|----|------|----------|
| T-113 | Configure PyInstaller spec file: bundle all Python packages, language files, assets, and the `platform/` modules. Exclude model files. | 16.1.a–b |
| T-114 | Write the Inno Setup script: installation path selection (default `%LOCALAPPDATA%\SpeechRecognitionProgram`), disk space check, VLC detection/download, HuggingFace licence page, Whisper model selection screen, model download with retry, desktop shortcut, Start Menu entry. | 16.1–16.4 |
| T-115 | Implement the installer's model download component: show progress per model file, delete partial files on failure, offer retry without restarting setup. | 16.1.d |
| T-116 | Implement the HuggingFace licence page in the installer: display licence text, require acceptance before proceeding, write `licence_accepted` flag to the installation folder. | 16.1.e, 4.7.a |
| T-117 | Implement the Whisper model selection screen in the installer: show size/speed/accuracy table, default to medium, allow user selection. | 16.1.f |
| T-118 | Test installer on a clean Windows 10 VM (no Python, no VLC pre-installed). | 16.1.a |
| T-119 | Test installer on a clean Windows 11 VM. | 16.1.a |
| T-120 | Update `BUILD.md` with final installer build steps and all Inno Setup parameters. | 16.4.c |

### Checks and Tests — Phase 7

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-123 | MT | Run installer on clean Windows 10. Application starts after installation. All nine GUI panels open. Processing a short audio file produces output. | 16.1.a |
| CHK-124 | MT | Run installer on clean Windows 11. Same validation as CHK-123. | 16.1.a |
| CHK-125 | MT | Installer disk space check: simulate <10 GB free (using a small volume). Installer aborts with a message showing required and available space. | 16.3.a–b |
| CHK-126 | MT | Installer with VLC not present: VLC is downloaded, installed system-wide, visible in Programs and Features. User is informed on the summary screen. | 16.1.c |
| CHK-127 | MT | Installer with VLC already present: no second VLC download occurs. Existing VLC is used. | 16.1.c |
| CHK-128 | MT | Model download failure: disconnect internet mid-download. Installer shows error and retry button. After reconnect and retry, download completes without restarting setup. No partial files remain in the installation folder. | 16.1.d |
| CHK-129 | MT | Decline the HuggingFace licence in the installer. Installation completes. On first launch, speaker identification features are disabled and a warning is displayed. | 4.7.b |
| CHK-130 | MT | Accept the HuggingFace licence in the installer. On first launch, speaker identification works. | 4.7.a |
| CHK-131 | MT | Select "tiny" model during installation. Verify that only the tiny model files are downloaded. | 16.1.f |
| CHK-132 | MT | Select custom installation path `C:\MyApps\WSP`. All files, config, and user data are created under `C:\MyApps\WSP`. No files are created in `%LOCALAPPDATA%`. | 16.2.a–b |
| CHK-133 | MT | Desktop shortcut and Start Menu entry exist after installation. Both launch the application. | 16.4.a |
| CHK-134 | MT | Uninstall the application (via Programs and Features). Application folder is removed. Shortcuts are removed. | — |
| CHK-135 | MT | Install on a machine where a second Windows user account exists. The second account has no access to the first account's installation or data. | 16.2.c |

---

## Phase 8 — Integration, Performance, and Regression Testing

**Goal:** End-to-end testing of the complete application across all major workflows.

### End-to-End Scenario Tests

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-136 | IT | **Full pipeline (file):** Process a 2-minute two-speaker English MP3 via GUI. Result: two speaker labels in output, English detected, TXT and JSON files written with correct field content. | 3.5, 4, 8 |
| CHK-137 | IT | **Full pipeline (translation):** Process a Finnish WAV. Translate to English via OPUS-MT. Output text is in English; language prefix shows "Finnish:". | 3.3, 6 |
| CHK-138 | IT | **Full pipeline (microphone, Regular mode):** Record and process 30 seconds of speech. Output written to file and displayed in GUI. Completion sound plays. | 12.6.a |
| CHK-139 | IT | **Full pipeline (Short Session mode, GUI visible):** Record a 10-word sentence with translation enabled. Fields populated after pipeline. Clipboard holds translated text. Edit first field, click "Translate and save to clipboard" — second field updates, clipboard updated. Edit second field, click "Save to clipboard" — clipboard updated again. Three distinct clipboard writes verified. | 12.6.b–d |
| CHK-140 | IT | **Batch queue (3 files):** Queue MP3, WAV, and AVI files. Process all three. Three output files created with correct `_WSP` naming. Error pop-up absent (no errors). | 9 |
| CHK-141 | IT | **Batch queue with one bad file:** Queue 3 files where file 2 is corrupt. File 2 is skipped. Files 1 and 3 produce output. Error pop-up lists file 2. | 9.2 |
| CHK-142 | IT | **Speaker identification:** Create a voice profile for Speaker A. Process an audio file containing Speaker A. Speaker A is correctly identified without a post-session naming prompt. | 4.1–4.3 |
| CHK-143 | IT | **Stream splitting:** Process a synthetic audio file of exactly 5 hours 2 minutes. Two output files are produced: `_part1` and `_part2`. Speaker numbering is continuous across the split. | 2.3 |
| CHK-144 | IT | **Voice library retraining:** Update the Whisper model (simulate checksum change). On startup, retraining prompt appears. Retrain. Summary shows all profiles retrained. Processing works correctly afterwards. | 4.6 |
| CHK-145 | IT | **Backup and restore round-trip:** Create a full backup. Modify settings, add a profile, add a dictionary entry. Restore the backup. All three changes are reverted. | 14 |
| CHK-146 | IT | **CLI batch processing:** `wsp.exe --input a.mp3 b.wav --output-format txt json`. Two input files produce four output files (`.txt` and `.json` for each). Exit code 0. | 15 |
| CHK-147 | IT | **No GPU:** Disable CUDA (set `CUDA_VISIBLE_DEVICES=-1`). Process a 60-second file on CPU. Output is produced (no crash). | 1.2.b |

### Performance Tests

| ID | Type | Description | Target |
|----|------|-------------|--------|
| CHK-148 | PT | Process a 10-minute English WAV on CUDA (RTX 3060 Ti). Measure total wall time (diarization + transcription). | < 3 minutes |
| CHK-149 | PT | Process a 10-minute English WAV on CPU only. Measure total wall time. | < 15 minutes |
| CHK-150 | PT | Application startup time (cold start, models loaded): time from launch to GUI ready. | < 10 seconds |
| CHK-151 | PT | GUI responsiveness: process a file in the background while scrolling the output text area. UI must remain responsive (no freeze). | No visible freeze |
| CHK-152 | PT | Memory usage during processing of a 30-minute file on CPU: peak RAM must remain below 8 GB. | < 8 GB RAM |
| CHK-153 | PT | Retraining of 20 speaker profiles on CUDA. Measure total time. | < 5 minutes |

### Regression Tests

| ID | Type | Description |
|----|------|-------------|
| CHK-154 | RT | Re-run all unit tests (CHK-06 through CHK-93) after any change to the pipeline, library, or config modules. |
| CHK-155 | RT | Re-run all GUI manual tests (CHK-96 through CHK-122 and CHK-163 through CHK-176) after any GUI change. |
| CHK-156 | RT | Re-run all installer tests (CHK-123 through CHK-135) before any release build. |
| CHK-157 | RT | Verify `requirements.txt` matches the actual installed environment after any library addition or version change. |

---

## Phase 9 — Documentation and Release

**Goal:** Produce final documentation and publish the first GitHub Release.

### Tasks

| ID | Task | Spec ref |
|----|------|----------|
| T-121 | Write `README.md`: purpose, features, system requirements, quick-start instructions, link to full docs. | 1.3.d |
| T-122 | Write `docs/CLI.md` (finalise from T-07): complete parameter reference with examples for every operation in Section 15.2. | 15 |
| T-123 | Finalise `BUILD.md`: complete step-by-step installer build instructions matching the final Inno Setup script. | 16.4.c |
| T-124 | Validate all 7 supported UI languages render correctly in the GUI (no truncation, no missing translations). Flag Russian and Chinese as pending native-speaker review in release notes. | 12.1.e |
| T-125 | Write release notes for v1.0: version number, release date, list of features, known issues (including Russian/Chinese translation quality), list of libraries and licences. | 1.3.e |
| T-126 | Publish GitHub Release v1.0: attach the installer, the approved wireframe PDF, and the release notes. | 1.3.e, 12.8.d |

### Checks and Tests — Phase 9

| ID | Type | Description | Spec ref |
|----|------|-------------|----------|
| CHK-158 | MT | All 7 UI languages: switch to each language in settings. Verify all main window controls, settings panel, and at least 3 other panels display translated text (no English fallback strings except Russian and Chinese pending review). | 12.1.b |
| CHK-159 | MT | Russian UI language: all standard controls display Cyrillic text. Mark as pending native-speaker review in release notes. | 12.1.e |
| CHK-160 | MT | `README.md` quick-start instructions: a new user following the README installs the application and successfully processes a WAV file within 30 minutes. | — |
| CHK-161 | MT | GitHub Release page: installer download link works. Release notes present. Wireframe PDF attached. | 1.3.e |
| CHK-162 | MT | Install from the GitHub Release asset on a clean Windows 11 VM. Application runs successfully. | 1.3.e |

---

## Summary Table

| Phase | Focus | Key outputs |
|-------|-------|-------------|
| 0 | Setup and research | Repo, stubs, wireframes (incl. two-field form amendment), test fixtures, CLI spec |
| 1-A | Audio ingestion | `audio.*` modules, FFmpeg extraction |
| 1-B | Diarization | `diarization.*` modules, licence check |
| 1-C | Transcription | `transcription.*` modules, bad-audio detection |
| 1-D | Substitution dictionary | `dictionary.*` modules, CSV import/export |
| 1-E | Translation | `translation.*` modules, OPUS-MT + Google |
| 1-F | Output writers | TXT, DOCX, SRT, JSON, clipboard writers |
| 2 | Voice library | Profile storage, retraining, import/export |
| 3 | Session history | Session save/load, output regeneration |
| 4 | Configuration and backup | Config system, backup/restore |
| 5 | CLI | Full command-line front-end |
| 6 | GUI | All panels, tray, hotkeys, playback, Short Session two-field form |
| 7 | Installer | Inno Setup + PyInstaller installer |
| 8 | Integration and performance | End-to-end, performance, regression |
| 9 | Documentation and release | README, CLI docs, GitHub Release v1.0 |

**Total tasks:** 133
**Total checks/tests:** 176

---

*End of Work Plan*

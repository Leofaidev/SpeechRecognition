# Speech Recognition Program — Technical Specification
**Version 1.0 · Final**

---

## Section 1 — Overview and Objectives

### 1.1 Purpose

This document specifies the full requirements for a locally executed, GPU-accelerated speech recognition application written in Python. The application converts spoken audio into text, identifies individual speakers, optionally translates the result, and delivers output in multiple configurable formats.

### 1.2 Target Platform

- a. Operating system: Windows 10 and Windows 11 (64-bit).
- b. Primary GPU: NVIDIA RTX 3060 Ti via CUDA. The application must also run on CPU without a GPU.
- c. Future platforms (Ubuntu, Debian, macOS) and accelerators (AMD ROCm, Intel OpenVINO, Apple CoreML/MPS, Qualcomm AI Engine) must be planned for through platform abstraction stubs (see Section 17) but are not implemented in version 1.

### 1.3 General Constraints

- a. All core processing (speech recognition, speaker identification) must run locally without external AI services.
- b. Translation is the only function that may optionally use an external service (see Section 6).
- c. All libraries used must be free and open-source. Every library must be listed in `requirements.txt` from the start of development.
- d. All source code and build artifacts must be maintained in a private GitHub repository. No branching strategy, CI/CD pipeline, or commit convention is required.
- e. Each release must be published as a GitHub Release with the installer attached and release notes containing: version number, release date, new features, bug fixes, and known issues (in English).

---

## Section 2 — Audio Input

### 2.1 Supported Input Sources

The application must accept audio from the following sources:

- a. **File input:** MP3, WAV, MP4, and AVI files. For MP4 and AVI files, the audio track is extracted using FFmpeg; only the audio is processed.
- b. **Microphone:** any microphone device recognised by the operating system, captured via pyaudio.
- c. **Webcam:** the audio track of any webcam recognised by the operating system. Video frames are accessed via OpenCV; audio is captured via pyaudio.

### 2.2 Input Device Selection

- a. The active input device (microphone, webcam, or line input) is selected from a dropdown control visible in the main application window, providing quick switching without opening settings.
- b. The selected device is saved persistently in the configuration file and restored on next launch.
- c. A real-time signal level meter is displayed in both the main window (beside the device dropdown) and in the settings panel. The meter shows live input amplitude continuously while a device is selected; no manual trigger is required.
- d. The input device can also be specified on the command line using the `--input-device` parameter (see Section 15.2). The program matches devices by case-insensitive partial name. If multiple devices match, the first match is used and a warning is printed. If no device matches, the program exits with an error that lists all available devices.

### 2.3 Stream Duration and Splitting

- a. The maximum continuous audio stream duration is 5 hours for all input types (files, microphone, webcam).
- b. When a stream reaches the 5-hour boundary, it is split into a new output file automatically and without user notification. Speaker numbering is not reset at the split point.
- c. Split output files are named using the standard `_WSP` naming convention (see Section 8.3) with sequential suffixes: `_part1`, `_part2`, `_part3`, and so on.
- d. For batch file processing, a file longer than 5 hours appears as a single queue item; splitting is transparent to the queue and produces multiple output files automatically.

---

## Section 3 — Speech Recognition

### 3.1 Recognition Engine

- a. Speech-to-text conversion is performed by Whisper or faster-whisper, both of which support CUDA acceleration on compatible NVIDIA hardware and fall back to CPU automatically.
- b. The application supports all languages that the selected Whisper model can recognise. No restriction is imposed on source languages.
- c. The user may either allow the application to detect the spoken language automatically, or specify the source language manually in the settings.

### 3.2 Whisper Model Selection

- a. Whisper is available in five sizes: tiny, base, small, medium, and large. Each size offers a different trade-off between download size, processing speed, and accuracy.
- b. During installation the user is presented with a model selection screen showing the size, speed, and accuracy characteristics of each option. The default pre-selected option is **medium**.
- c. The selected model is downloaded during installation. The user may change the model size later in the application settings, which triggers a new download.
- d. The application stores the SHA-256 checksum of the installed model files at installation time. On every startup the checksum of the current model files is recomputed and compared with the stored value. A mismatch triggers the voice library retraining workflow (see Section 4.6), regardless of how the model was updated.

### 3.3 Language Identification Output

- a. When automatic language detection is active and the Language field is enabled in the output content configuration (Section 8.4), the detected source language name is prepended to each recognised segment (e.g. `Finnish: ...`).
- b. When translation is also active, the language prefix still identifies the detected source language; the segment body is in the target translation language.
- c. When the Language field is disabled in the output content configuration, no prefix is prepended regardless of whether automatic detection is active.

### 3.4 Bad Audio Detection

- a. If Whisper reports a `no_speech_prob` value greater than 0.6 for any segment, that segment is considered unrecognised.
- b. Unrecognised words within a segment are replaced with `XXXXX` in the output text.
- c. A global "bad audio" warning indicator is displayed once per processed file. For microphone or webcam sessions, the indicator is shown once per session.

### 3.5 Processing Pipeline

The application processes audio in the following fixed sequence:

1. **Speaker diarization:** pyannote.audio segments the audio by speaker before transcription.
2. **Speech-to-text:** each speaker segment is transcribed individually by Whisper or faster-whisper.
3. **Language detection:** the source language is identified from the transcribed text.
4. **Substitution dictionary:** matching words are replaced according to the global dictionary (see Section 7).
5. **Translation:** if enabled, the substituted text is translated into the selected target language (see Section 6).
6. **Output:** the final text is written to all active output destinations (see Section 8).

---

## Section 4 — Speaker Identification

### 4.1 Diarization

- a. Speaker diarization is performed by pyannote.audio. The audio is segmented by speaker before transcription; each segment is then transcribed individually.
- b. The application supports up to 10 simultaneous speakers per session.
- c. Speaker segments shorter than 10 seconds are transcribed normally but are flagged with a low speaker identification confidence score. If the confidence score falls below the configured threshold, the speaker is labelled Unknown.
- d. The use of pyannote.audio requires acceptance of the HuggingFace licence (see Section 4.7). If the licence has not been accepted, diarization and all speaker identification features are disabled.

### 4.2 Speaker Numbering During a Session

- a. When an unrecognised speaker (not present in the voice library) is detected during a microphone or file session, they are assigned a temporary label: Speaker 1, Speaker 2, and so on, in the order they are first detected.
- b. Speaker numbers are reset to 1 at the start of each new session or batch.
- c. Speakers already present in the active voice library group are identified automatically; they do not receive a temporary Speaker N label.

### 4.3 Post-Session Speaker Labelling

- a. Immediately after a session or batch ends, the application presents the speaker labelling prompt for each speaker that was not identified from the library.
- b. For each unidentified speaker in order (Speaker 1, Speaker 2, …), the application plays the captured audio fragment and prompts the user to enter the speaker's metadata: last name, first name, and optionally middle name, nickname, organisation, position, and note.
- c. The user may click Skip for any speaker. Skipped speakers retain their Speaker N label in the output. Their profiles can be completed later using the Voice Profile Management panel (Section 5).
- d. All segments belonging to a confirmed speaker are retroactively relabelled with the speaker's full name before output is written, regardless of when in the session the identification was confirmed.
- e. Output is written immediately after all labelling prompts are completed or skipped, using whatever labels are available at that point.
- f. The post-session labelling prompt applies to both file/batch input and microphone/webcam input.

### 4.4 Speaker Groups

- a. Speakers in the voice library can be organised into named groups. Speaker identification is performed only against the speakers in the currently active group.
- b. The active group is set by the user in the main application window or in settings. The last used group is restored automatically on startup. On first launch, a default group named "Group 1" is created containing all library profiles.
- c. If the active group contains no profiles, speaker identification is skipped for that session and all speakers are treated as unknown.
- d. Group management (create, rename, delete, add/remove members) is performed in the Voice Profile Management panel (Section 5). A speaker may belong to multiple groups. There is no limit on the number of groups or members per group. Groups are saved permanently.
- e. Deleting a speaker profile automatically removes that speaker from all groups. Renaming a profile automatically updates all group memberships.

### 4.5 Voice Library Storage

- a. Each speaker profile is stored in a dedicated subfolder within the voice library folder. The subfolder name is formed by joining the speaker's last name, first name, middle name, and nickname with underscores (e.g. `Smith_John__`). Empty name fields produce empty strings between underscores. Characters that are invalid in Windows folder names are replaced with underscores.
- b. For profiles where all four name fields are empty, a unique numeric ID (e.g. `001`) is appended to prevent folder name collisions. This ID is stored in the nickname field with the reserved prefix `#` (e.g. `#001`) to distinguish it from a user-entered nickname. When the user fills in any real name field via the profile editor, the auto-assigned nickname is cleared automatically unless the user explicitly replaces it.
- c. Each profile subfolder contains: one or more MP3 voice samples (named `sample_001.mp3`, `sample_002.mp3`, …), a model embedding vector file generated by pyannote.audio, and a metadata file named `speaker.json`.
- d. The `speaker.json` file contains: last name, first name, middle name, nickname, organisation, position, note (all fields stored with their original characters), creation date, SHA-256 checksum of the model version at creation time, number of samples used in the most recent retraining, list of associated MP3 sample filenames, and list of groups the speaker belongs to.
- e. All name fields in `speaker.json` are optional. Profiles with all name fields empty are displayed in the application UI as `___001` and are shown with a visual indicator prompting the user to complete the profile.

### 4.6 Voice Library Retraining

- a. Speaker embeddings must not be tied to a specific version of the pyannote.audio or Whisper model. On every startup, the application computes the SHA-256 checksum of the current model files and compares it against the checksum recorded at the last successful retraining.
- b. If the checksums differ, the application prompts the user to retrain the voice library before proceeding. Retraining cannot be skipped.
- c. Retraining reprocesses all available MP3 samples for every speaker through the updated model. All samples for a given speaker are combined into a single averaged embedding vector; more samples improve identification accuracy. The `speaker.json` file is updated with the new model checksum and sample count.
- d. Retraining runs in the foreground with a progress indicator. On completion, a summary is displayed showing: total speakers retrained, total samples processed, and the names of any profiles that failed (e.g. due to missing or corrupted MP3 files).
- e. As an alternative to retraining, the user may choose to revert to the previous model version. Reverting requires re-downloading the old model from the internet; the user is informed of this before confirming. The application reverts to the model version recorded at the last successful retraining.
- f. On first launch after installation, if the voice library is not empty and no retraining history exists, the application runs an initial retraining pass automatically before proceeding. If the library is empty, this step is skipped.

### 4.7 HuggingFace Licence Acceptance

- a. The pyannote.audio library requires acceptance of the HuggingFace licence agreement. During installation, the installer presents the licence text and requires the user to accept or decline it before installation can proceed.
- b. On every startup, the application checks whether the licence has been accepted. If it has not, all pyannote.audio-dependent features are disabled: diarization, automatic speaker identification, and the manual speaker marking interface. All speakers are labelled Unknown and a persistent warning is displayed in the application window.
- c. The user may accept the licence at any time from the application settings. Acceptance takes effect after the application is restarted; the user is informed of this requirement with a prompt.
- d. After restarting with the licence accepted, previously processed files can be reprocessed manually by adding them to the batch queue or processing them as single files.
- e. In command-line mode, if the licence has not been accepted, a warning is printed to standard output at the start of processing and execution continues with all speakers labelled Unknown.

---

## Section 5 — Voice Profile Management

### 5.1 Management Panel

A dedicated Voice Profile Management panel is accessible from the main application window. The panel is divided into two sections: a speaker list on the left and a group list on the right. The user can drag speakers into groups or use add/remove buttons. All profile and group operations described below are performed from this panel.

### 5.2 Profile Operations

- a. **Create:** A new profile is created by providing an audio file (MP3, WAV, MP4, or AVI). Audio is extracted via FFmpeg if needed. The create dialog includes audio playback (via python-vlc) and a draggable start marker that lets the user select the 10-second segment to use as the voice sample. The default start position is the beginning of the file. The application extracts the selected 10 seconds, generates an embedding vector using pyannote.audio, and saves `sample_001.mp3` and the vector file to a new speaker subfolder. The current model checksum is recorded in `speaker.json`.
- b. **Edit:** Opens the full profile editor for all metadata fields: last name, first name, middle name, nickname, organisation, position, and note. The subfolder name is updated automatically when name fields change. All group memberships referencing the old name are updated to the new name automatically.
- c. **Delete:** Removes the selected profile and its entire subfolder (all MP3 samples, embedding vector, and `speaker.json`). Supports bulk deletion of multiple profiles. The deleted speaker is automatically removed from all groups.

### 5.3 Short Sample Handling

If the audio provided for profile creation is shorter than 10 seconds, the user is warned. The profile is created with the available audio but is flagged with a low confidence indicator in the profile list.

### 5.4 Conflict Resolution on Create

If a profile with the same full name already exists when a new profile is being created, a dialog offers three options:

- a. **Overwrite:** the existing profile is replaced entirely by the new one.
- b. **Merge:** the new MP3 sample is added as the next sequential sample (`sample_002.mp3`, etc.) alongside the existing samples. Embeddings are not regenerated automatically; the user must trigger retraining manually.
- c. **Reject:** the create operation is cancelled and the existing profile is preserved unchanged.

### 5.5 Import and Export

- a. **Export:** produces a ZIP archive containing the selected speaker subfolders (all MP3 samples, embedding vectors, and `speaker.json` files). Multiple speakers may be selected for a single export. Group membership data is embedded in each `speaker.json` and is therefore included automatically.
- b. **Import:** accepts a ZIP archive in the same format. For each imported profile, if a profile with the same full name already exists, the conflict resolution dialog (Section 5.4) is shown. Groups referenced in the imported `speaker.json` files are created automatically if they do not already exist on the target system.
- c. Immediately after an import completes, the application triggers the voice library retraining prompt (Section 4.6) before the newly imported profiles become active.

### 5.6 Full Name Output Format

The format used to display and output a speaker's full name is configurable in the application settings. The user selects which metadata components to include and in what order from: last name, first name, middle name, nickname, organisation, and position. A live preview using a sample profile is shown in the settings panel. The note field is internal only and never appears in any output.

---

## Section 6 — Translation

### 6.1 Translation Overview

- a. Translation is performed after the substitution dictionary has been applied (step 5 of the processing pipeline, Section 3.5).
- b. Translation may be left disabled, in which case output is produced in the recognised source language.
- c. When translation is enabled, the application displays only the translated text in the output; the source-language text is not shown separately.

### 6.2 Supported Target Languages

The following translation target languages are supported in version 1:

- English
- Spanish
- Finnish
- Russian
- Chinese Simplified (zh-Hans)
- Chinese Traditional (zh-Hant)

Additional target languages can be added by the user via configuration files. The translation language list is independent of the UI language list.

### 6.3 Translation Engines

- a. **Local (OPUS-MT):** translation is performed using the Helsinki-NLP OPUS-MT library. OPUS-MT language model files are downloaded on first use of each specific source-target language pair. A progress indicator is displayed during the download. For language pairs where OPUS-MT coverage is limited (particularly pairs involving Chinese), a quality warning is displayed in the settings panel next to the affected pair, recommending the use of Google Translate for better results.
- b. **Online (Google Translate):** translation is performed using the free Google Translate service. If the online service is unavailable or returns an error, an error message is displayed and translation stops; the application does not fall back to OPUS-MT automatically.
- c. The active translation engine (local or online) is selected by the user in the application settings. The selection is saved persistently.

### 6.4 Translation Timing

- a. For microphone and webcam input, translation is performed after the recording session ends, not in real time during recording.
- b. For file input, translation is performed as part of the standard processing pipeline after transcription.
- c. There are no speed requirements for translation.

---

## Section 7 — Substitution Dictionary

### 7.1 Purpose and Scope

The substitution dictionary is a global, session-independent table of word replacements. It is applied during every recognition session, after transcription and language detection but before translation (step 4 in the pipeline, Section 3.5). The dictionary is not applied during voice library retraining.

### 7.2 Matching Rules

- a. Matching is case-insensitive.
- b. Only whole words are matched; partial matches within longer words are not replaced.
- c. Wildcard matching is supported using fnmatch syntax: the asterisk (`*`) matches any sequence of zero or more characters; the question mark (`?`) matches exactly one character.
- d. Substituted words are passed to the translation engine as-is. The user is responsible for ensuring that substitution values are appropriate for the target translation language.
- e. Substitution replacements do not affect speaker identification confidence scores, which are computed from the raw audio and transcription before any substitution is applied.

### 7.3 Dictionary Management

- a. The dictionary is displayed and edited as a table in the application UI. It is accessible both from a standalone panel in the application settings and from within an active session.
- b. The dictionary table supports its own undo/redo history, independent of the speaker marking undo/redo history.
- c. The dictionary can be exported to a CSV file and imported from a CSV file.
- d. On import, new entries (source words not already in the dictionary) are added automatically. Entries whose source word conflicts with an existing entry are rejected; they are not merged or overwritten. A summary is displayed after import showing: total entries in the imported file, number of entries added, number of entries rejected, and the list of rejected source words.
- e. The same summary is printed to standard output when the import is performed via the command line (see Section 15.2).

---

## Section 8 — Output

### 8.1 Output Destinations

The user specifies one or more active output destinations in the application settings. Multiple destinations may be active simultaneously. Available destinations are:

- a. **Display:** the recognised text is shown in the application's main window.
- b. **File:** the text is saved to a file in one or more of the following formats: plain text (`.txt`), Microsoft Word (`.docx`), SRT subtitles (`.srt`), or JSON (`.json`). Each enabled file format produces a separate output file.
- c. **Clipboard:** the text is copied to the system clipboard. Clipboard output is available for microphone and webcam input only. For file and batch input, clipboard output is silently ignored. If clipboard is the only active destination and the input source is a file or batch, an informational message is displayed explaining the restriction.

### 8.2 Output Folder

- a. All file output (single file and batch) is written to a single user-specified output folder. This folder is configured in the application settings and saved persistently.
- b. The default output folder is the application installation folder.
- c. The output folder can also be specified on the command line (see Section 15.2).

### 8.3 Output File Naming

- a. Output files are named after the input file with the suffix `_WSP` appended before the file extension (e.g. `interview_WSP.txt`).
- b. If a file with the same name already exists in the output folder, a numeric suffix is appended and incremented until a unique name is found (e.g. `interview_WSP_2.txt`, `interview_WSP_3.txt`).
- c. For streams split at the 5-hour boundary (Section 2.3), the part suffix precedes the extension (e.g. `interview_WSP_part1.txt`, `interview_WSP_part2.txt`).

### 8.4 Output Content Configuration

- a. The user configures which data fields are included in the output using the Output Content Configuration panel. This configuration applies to all output formats. It is saved as a single persistent profile between sessions.
- b. The following fields are individually selectable:
  - **Language:** the detected source language name, prepended to the segment text when enabled (see Section 3.3).
  - **Speaker name:** formatted according to the full name format configured in Section 5.6.
  - **Start time:** the absolute start time of the segment from the beginning of the file or recording, in `HH:MM:SS,mmm` format.
  - **Transcription confidence:** Whisper's per-segment confidence metric, expressed as a decimal to 5 decimal places.
  - **Speaker identification confidence:** pyannote.audio's speaker match confidence, expressed as a decimal to 4 decimal places (range 0.0000–1.0000).
  - **Speech text:** the recognised (and optionally translated) text of the segment.
- c. For plain text (`.txt`) and Word (`.docx`) output, each selected field appears on a separate line within each segment block. Segment blocks are separated by a blank line. In `.docx` output, each segment block is a distinct paragraph.
- d. For SRT output, field selection does not apply. SRT output always contains the standard SRT timestamp, the speaker name (when available), and the speech text only. The language prefix is suppressed in SRT output. SRT timestamps use the format `HH:MM:SS,mmm` and correspond directly to segment start times with no offset adjustment.
- e. For JSON output, all six fields are always present regardless of field selection. The output content configuration controls which fields appear in text and Word output only.

---

## Section 9 — Batch Processing

### 9.1 Queue Management

- a. Multiple files can be added to a processing queue instead of processing each file individually.
- b. The queue operates on a strict first-in, first-out (FIFO) principle. Reordering of queued items is not supported.
- c. Before processing starts, the user may add files to or remove files from the queue. Once processing begins, the queue is locked and cannot be modified.

### 9.2 Error Handling

- a. If a file in the queue fails to process, the application skips that file, logs the error, and continues with the next item.
- b. At the end of the batch, a pop-up window lists all files that were not successfully processed.

### 9.3 Batch Output

Batch output follows the file naming rules in Section 8.3. Each input file produces a separate output file (or set of files for multiple formats). All output is written to the folder specified in Section 8.2.

---

## Section 10 — Audio Playback

### 10.1 Playback in the Main Window

- a. The application supports in-window audio playback for processed files. Supported playback formats: MP3, WAV, MP4, AVI. Playback is handled by python-vlc.
- b. A seek slider allows the user to scrub to any position in the audio.
- c. Clicking on a speaker start time in the output text jumps playback to that position. The seek slider and click-on-timestamp interactions work simultaneously.
- d. Playback is disabled during active recording sessions.

### 10.2 Playback in the Voice Profile Create Dialog

The voice profile creation dialog (Section 5.2) includes audio playback of the provided sample file, a draggable start marker for selecting the 10-second extraction window, and a preview function that plays the selected 10-second segment before confirmation. Playback in this dialog also uses python-vlc.

---

## Section 11 — Session History

### 11.1 Storage

- a. After every processing session (file, batch, or microphone), the full transcription result is saved as a JSON file in a `sessions` subfolder within the application installation folder.
- b. Sessions are retained indefinitely. There is no automatic deletion. The user may manually delete sessions from the Session History panel.
- c. There is no limit on the number of stored sessions.

### 11.2 Output Regeneration

- a. The user may regenerate output files for any session stored in the session history without reprocessing the original audio.
- b. Regeneration uses the stored transcription data and applies the current output content configuration at the time of regeneration. This allows the user to produce output with different fields or formats than the original.
- c. Regenerated files follow the same naming convention as Section 8.3. If the original output file still exists, the numeric suffix rule applies (e.g. `interview_WSP_2.txt`).

### 11.3 Outdated Output Indicators

- a. When a speaker's profile metadata is edited (e.g. name, organisation), all session history entries that reference that speaker are flagged with an "output outdated" indicator.
- b. The user may choose to regenerate the affected output files from the Session History panel.
- c. Output files are never updated automatically when profile metadata changes.

### 11.4 Command-Line Access

Session history is accessible from the command line:

- `wsp.exe --list-sessions` — prints a list of all stored sessions with their IDs and dates.
- `wsp.exe --regenerate-output --session "<session_id>" --output-folder "<path>"` — regenerates output files for the specified session.

---

## Section 12 — Graphical User Interface

### 12.1 Framework and General Requirements

- a. The GUI is built using CustomTkinter.
- b. The UI language is selectable in the application settings. English is the default on first launch. Supported UI languages: English, German, Spanish, Finnish, Russian, Chinese Simplified, Chinese Traditional.
- c. UI language files use JSON format. Each language is defined in a separate file stored in a `languages` subfolder within the installation folder. A template and a README documenting all required keys are included in the installation folder.
- d. Built-in language files may be freely edited by the user. If a built-in file is missing or corrupted, the application displays an error and restores it from a protected backup copy stored in a subdirectory of the installation folder.
- e. Additional UI languages can be added by creating new JSON language files in the `languages` folder. The developer ships initial Russian and Chinese language files generated via automated translation; these are marked as pending native-speaker review and this limitation is noted in the release notes.
- f. Additional translation languages can be added by the user via configuration files, independently of the UI language.

### 12.2 Status Indicators

- a. **Recording indicator:** an animated pulsing dot displayed in the main window. The dot is red during active recording and grey when idle.
- b. **File-level progress bar:** shows processing progress through the current file or the current item in a batch queue.
- c. **Queue-level progress bar:** shows overall batch progress (e.g. "File 3 of 12"). This bar is visible only during batch processing.

### 12.3 Main Window Controls

The main window must include at minimum:

- Input device dropdown (see Section 2.2)
- Signal level meter (see Section 2.2)
- Recording mode toggle: Regular or Short Session (see Section 12.6)
- Recording indicator and progress bars (see Section 12.2)
- Active group selector (see Section 4.4)
- Text display area — in Regular mode: a single output text display area; in Short Session mode: a two-field interactive form (see Section 12.6.b and 12.6.d)
- Audio playback controls and seek slider (see Section 10.1)

### 12.4 UI Panels

The following panels must be accessible from the main window:

- **Settings** — all persistent configuration options
- **Voice Profile Management** — speaker and group management (Section 5)
- **Substitution Dictionary** — dictionary table and import/export (Section 7)
- **Batch Queue** — file queue and processing controls (Section 9)
- **Output Content Configuration** — field selection and format settings (Section 8.4)
- **Hotkey Configuration** — hotkey assignment (Section 12.5)
- **Speaker Labelling Prompt** — post-session speaker naming (Section 4.3)
- **Session History** — past sessions and output regeneration (Section 11)
- **Backup and Restore** — backup management (Section 14)

### 12.5 Hotkeys

- a. The application supports configurable global hotkeys that operate system-wide using the keyboard library, even when the application window is not in focus.
- b. Hotkeys can be configured on first launch or at any time in the Hotkey Configuration panel. The default bindings are:
  - Start recording: `Ctrl+Shift+R`
  - Stop recording: `Ctrl+Shift+S`
  - Copy to clipboard: `Ctrl+Shift+C`
- c. Default bindings are applied if the user skips the first-launch hotkey setup.
- d. When assigning a hotkey, the application checks for known conflicts with common Windows shortcuts and displays a warning. The user may proceed with the conflicting assignment or choose a different combination.
- e. Hotkeys are completely disabled in command-line mode.

### 12.6 Recording Modes

- a. **Regular mode:** the user starts and stops recording explicitly using the hotkeys or UI controls. After recording ends, the full processing pipeline runs (Sections 3–6) and output is written to all active destinations.
- b. **Short session mode — pipeline sequence:** intended for dictating short AI prompts or podcast speech. The pipeline sequence is: (1) user presses the start hotkey — recording begins; (2) user presses the stop hotkey — recording ends; (3) transcription runs; (4) substitution dictionary is applied; (5) translation runs if enabled; (6) result is copied to the system clipboard automatically, regardless of the general output destination settings; (7) other active output destinations (display, file) also receive the result; (8) the completion sound plays (Section 12.7); (9) if the main window is visible and not minimised to the tray, the two-field interactive form is populated (see Section 12.6.d).
- c. The recording mode is toggled in the main application window. The selected mode is saved and restored on restart. Mode switching is not available from the system tray; the tray menu shows the current mode as read-only text.
- d. **Short session mode — two-field interactive form (GUI visible only):** When the main window is visible and not minimised to the tray, Short Session mode displays a two-field interactive form in place of the single output text display area. When the window is minimised to the tray, Short Session mode operates in "run once and forget" mode — the pipeline runs silently, the clipboard is written automatically, the beep plays, and no form is shown.

  **Form layout:**
  - The first field displays the untranslated transcribed text and is editable. Next to it is a button labelled **"Translate and save to clipboard"** when translation is enabled, or **"Copy to clipboard"** when translation is disabled. The button label updates dynamically when the translation setting changes.
  - The second field displays the translated text and is editable. Next to it is a button labelled **"Save to clipboard"**.
  - When translation is disabled, the second field and its "Save to clipboard" button are hidden. The first field and its button expand to fill the available space.
  - Both fields support standard OS-level undo/redo (Ctrl+Z / Ctrl+Y) within each field independently. This is isolated from the speaker marking and dictionary undo/redo histories.

  **Post-pipeline steps (appended after step 9):**
  - Step 10: The untranslated text produced by the pipeline is placed in the first field. The translated text (if translation is enabled) is placed in the second field. Both fields are cleared at the start of each new recording.
  - Step 11 (user-initiated): The user edits the text in the first field and clicks "Translate and save to clipboard". The first field's current content is translated and placed in the second field and written to the clipboard. If translation is disabled, the first field's content is copied to the clipboard directly.
  - Step 12 (user-initiated): The user edits the text in the second field and clicks "Save to clipboard". The second field's current content is written to the clipboard.
  - If the user takes no action on the fields or buttons, the session operates in **"run once and forget"** mode — the fields retain their content until the next recording begins, at which point both fields are cleared.

  **Clipboard write sequence:** Up to three clipboard writes may occur in a single Short Session — (1) automatic write at step 6 of the pipeline; (2) optional write when "Translate and save to clipboard" or "Copy to clipboard" is clicked; (3) optional write when "Save to clipboard" is clicked. This is the intended and accepted behaviour.

  **"Translate and save to clipboard" button:** Clicking this button always overwrites the second field with a fresh translation of the current content of the first field, regardless of what the second field already contains.

  **Session history:** One session history record is created per recording (pipeline run). The record is updated each time the clipboard is written, always reflecting the most recently copied text. Only one record exists per recording regardless of the number of clipboard writes.

  **Wireframe amendment:** A wireframe amendment showing the two-field layout must be produced, attached to the existing GitHub issue as an addendum, and approved in writing by the commissioning party before development of this feature begins.

### 12.7 Completion Sound

- a. The application plays an audio completion signal when any processing run finishes. This applies to: end of a short session, end of a regular microphone or webcam session, end of single file processing, and end of batch processing.
- b. The completion sound is configurable in settings: it can be disabled, and the user can select a sound from a set of built-in options or provide a custom audio file.
- c. The completion sound is suppressed in command-line mode.

### 12.8 Wireframe Requirements

- a. During the research phase, three distinct UI design options must be produced as wireframes. Each option must cover all panels listed in Section 12.4 and present a consistent navigation and layout approach across all of them.
- b. Wireframes are delivered as a PDF document containing annotated static images of all panels for each option.
- c. The PDF is attached to a dedicated issue in the private GitHub repository. Development does not begin until the commissioning party records written approval as a comment on that issue.
- d. The approved wireframe PDF is also attached to the first GitHub Release as a permanent design reference.

---

## Section 13 — System Tray and Auto-Start

### 13.1 System Tray

- a. When "Minimize to tray" is enabled in settings, minimizing the main window removes it from the taskbar and places an icon in the Windows system tray.
- b. The tray icon provides a right-click context menu with the following items:
  - **Open** — restores the main window.
  - **Current mode** — read-only text showing the active recording mode (Regular / Short Session).
  - **Start recording** — greyed out when a session is already active.
  - **Stop recording** — greyed out when no session is active.
  - **Exit**
- c. The Start/Stop recording tray items operate in whichever recording mode is currently active, consistent with hotkey behaviour.
- d. When Exit is selected during an active recording or batch processing session, a confirmation dialog warns the user that processing is in progress and asks them to confirm or cancel the exit. If confirmed, the active session or batch is terminated and the application exits.

### 13.2 Tray Notifications

- a. When processing completes, a pop-up tray notification (balloon tooltip) is displayed. This notification fires at the same time as the completion sound (Section 12.7) and is fully independent of it.
- b. The tray notification can be independently enabled or disabled in settings.
- c. Tray notifications are suppressed in command-line mode.

### 13.3 Auto-Start

- a. When "Auto-start with Windows" is enabled in settings, the application launches automatically when the user logs in to Windows.
- b. Auto-start is implemented via the current user's HKCU registry key or startup folder. No administrator privileges are required. The implementation is documented in the settings UI.
- c. The auto-start registry entry is written when the user enables the setting and removed when they disable it. The installer does not create the auto-start entry.
- d. When both auto-start and minimize-to-tray are enabled, the application launches directly to the tray on Windows startup without showing the main window.

---

## Section 14 — Backup and Restore

### 14.1 Backup Contents

A backup archive (ZIP format) includes all of the following:

- Application configuration file
- Substitution dictionary
- Voice library: all speaker subfolders (MP3 samples, embedding vectors, `speaker.json` files)
- Speaker groups
- Output content configuration
- Session history JSON files

### 14.2 Creating a Backup

- a. The estimated backup size is displayed before the archive is created.
- b. The default backup folder is the application installation folder. This default is configurable in settings. If the backup folder is located inside the installation folder, the application and the restore dialog display a warning advising the user to store backups in a separate location.
- c. From the GUI, the default folder is pre-selected in the save dialog but the user may change it.
- d. From the command line: `wsp.exe --backup "<path>"`

### 14.3 Restoring a Backup

- a. Before performing a restore, the application automatically creates a backup of the current state. The backup location is shown to the user (or printed to standard output in command-line mode).
- b. Restore replaces all current settings and data with the contents of the archive after a confirmation prompt.
- c. From the command line: `wsp.exe --restore "<path>"`

---

## Section 15 — Command-Line Interface

### 15.1 General

- a. The application supports command-line operation for batch processing and data management tasks. In command-line mode, the GUI is not launched and the application exits with code 0 on success or a non-zero code on failure.
- b. All command-line output, including errors and warnings, is always in English regardless of the configured UI language.
- c. If the command line contains an unrecognised parameter, or references a speaker name or group that does not exist in the library, the application does not start and prints a specific error message identifying the exact problem.
- d. Parameters omitted from the command line default to the values from the last saved session configuration, except for the input file list, which is the only mandatory parameter for batch processing.
- e. If no input files are provided and no input files exist in the last session configuration, the application exits with a specific error message.
- f. The application supports `--help`, which prints all available parameters with descriptions and usage examples, then exits with code 0.
- g. The exact parameter names and syntax are defined by the developer during the research phase, following standard Windows CLI conventions (double-dash long parameters, single-dash short aliases), and documented in a README file included with the installation.
- h. The installer build process is documented in `BUILD.md` in the GitHub repository, including step-by-step instructions for producing the installer from source.

### 15.2 Available Operations

The following operations must be supported from the command line:

- a. **Batch processing:** specify input files, output folder, source language, translation target, speaker group, output formats, and input device.
- b. **Voice profile management:**
  - Create: `--profile-create --lastname --firstname [--middlename] [--nickname] [--organisation] [--position] [--note] --audio "<path>"`
  - Delete: `--profile-delete --name "<name>"`
  - Rename: `--profile-rename --name "<name>" --new-name "<new-name>"`
- c. **Dictionary management:**
  - Export: `--dict-export "<path>"`
  - Import: `--dict-import "<path>"`
- d. **Backup and restore:**
  - Create backup: `--backup "<path>"`
  - Restore backup: `--restore "<path>"`
- e. **Session history:**
  - List sessions: `--list-sessions`
  - Regenerate output: `--regenerate-output --session "<session_id>" --output-folder "<path>"`
- f. **Help:** `--help`

---

## Section 16 — Installer

### 16.1 Installer Requirements

- a. The application is distributed as a single executable installer built with PyInstaller and Inno Setup. The installer targets Windows 10 and Windows 11 (64-bit).
- b. The installer bundles all required Python packages, including the Helsinki-NLP OPUS-MT Python package (but not the language model files, which are downloaded on first use).
- c. VLC media player is required for playback (python-vlc). The installer checks whether VLC is already installed. If found, it is used as-is. If not found, the installer downloads and installs VLC as a standard system-wide installation visible in Windows Programs and Features. The user is informed on the installation summary screen.
- d. Whisper and pyannote.audio model files are downloaded from the internet during installation. If a download fails, the installer displays an error and offers a retry without restarting the full installation. On failure, partial download files are deleted before retrying.
- e. The installer presents the HuggingFace licence agreement for pyannote.audio and requires the user to accept or decline before proceeding (Section 4.7).
- f. The installer presents a Whisper model selection screen. The default selection is medium (Section 3.2).

### 16.2 Installation Path

- a. The default installation path is `%LOCALAPPDATA%\SpeechRecognitionProgram`. A dialog allows the user to select a custom path.
- b. All application files and user data (voice library, configuration, dictionaries, language files, session history, backups) are stored under the chosen installation path. There is no separate fixed user data location.
- c. Each Windows user account has an independent installation under their own `%LOCALAPPDATA%`. User data is never shared between Windows user accounts on the same machine.

### 16.3 Disk Space

- a. The installer checks available disk space at the selected installation path before beginning. The minimum required space is 10 GB, which covers all components including the largest Whisper model and all OPUS-MT language pair models.
- b. If available disk space is insufficient, installation is aborted with a message stating both the required and available space.
- c. The minimum space requirement is displayed on the installation summary screen.

### 16.4 Post-Installation

- a. The installer creates a desktop shortcut and a Start Menu entry.
- b. Silent/unattended installation is not required.
- c. The installer build process is documented in `BUILD.md` in the GitHub repository.

---

## Section 17 — Platform Abstraction

### 17.1 Principle

Although version 1 supports Windows only, the codebase must be structured from the outset to allow future ports to Ubuntu, Debian, and macOS, and to support hardware accelerators from AMD, Intel, Apple, and Qualcomm. All OS-specific and hardware-specific code must be isolated in dedicated platform modules.

### 17.2 Stub Modules

A stub module must be created for each platform-specific subsystem listed below. Each stub must raise `NotImplementedError` with a message identifying the unsupported platform. Stubs are created but not tested in version 1; testing is deferred until the platform is implemented.

- a. **Installer:** Windows — Inno Setup + PyInstaller (implemented). Stubs: `.deb` package (Ubuntu/Debian), `.pkg`/`.dmg` (macOS).
- b. **Auto-start:** Windows — HKCU registry key or startup folder (implemented). Stubs: XDG autostart (Linux), LaunchAgent plist (macOS).
- c. **System tray:** Windows — pystray or CustomTkinter tray (implemented). Stubs: Linux desktop environment tray, macOS NSStatusBar.
- d. **Data directories:** Windows — `%LOCALAPPDATA%` (implemented). Stubs: `~/.local/share` (Linux), `~/Library/Application Support` (macOS).
- e. **Global hotkeys:** Windows — keyboard library (implemented). Stubs: alternative implementations for Linux and macOS where the keyboard library has limited or no support. Developers working on non-Windows machines use a mock stub of the hotkey module for testing.
- f. **Hardware accelerators:** NVIDIA CUDA via CUDA toolkit (implemented). Stubs: AMD ROCm, Intel OpenVINO/IPEX, Apple CoreML/MPS, Qualcomm AI Engine SDK.
- g. **Input device enumeration:** Windows — pyaudio + OpenCV with Windows device APIs (implemented). Stubs: equivalent Linux (ALSA/PulseAudio) and macOS (CoreAudio) implementations.

---

## Section 18 — Preferred Libraries

The following libraries are preferred for the implementation. All must be free and open-source. All must be listed in `requirements.txt`.

| Library | Role |
|---|---|
| Whisper / faster-whisper | Speech-to-text and language detection (CUDA-compatible) |
| pyannote.audio | Speaker diarization (HuggingFace licence required; see Section 4.7) |
| FFmpeg | Audio extraction from MP4 and AVI files |
| CustomTkinter | Graphical user interface |
| pyaudio | Microphone and webcam audio capture |
| OpenCV | Webcam video stream access |
| keyboard | Global hotkeys (Windows; stub for other platforms) |
| Helsinki-NLP OPUS-MT | Local translation |
| python-vlc | Audio and video playback (requires VLC media player) |
| PyInstaller | Application bundling |
| Inno Setup | Windows installer creation |

---

*End of Specification*

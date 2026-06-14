# WSP UI Test Checklist

Manual regression tests for the Speech Recognition Program GUI.  
Each test row has two checkbox columns: **Win** (Windows 10/11) and **Lin** (Ubuntu 26.04).

Legend: ✅ pass · ❌ fail · ⚠️ partial · — not applicable on this platform

---

## 1. App Launch

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 1.1 | App starts without crash | Run `pythonw -m gui.app` from `src/` | Window appears with title "Speech Recognition Program" | - [ ] | - [ ] |
| 1.2 | Default state | On launch | Status label shows "Idle"; Start button enabled; mode = Regular | - [ ] | - [ ] |
| 1.3 | Window remembers size/position | Resize window, close, reopen | Window restores to last size and position | - [ ] | - [ ] |
| 1.4 | App icon in taskbar | On launch | WSP icon appears in the taskbar / dock | - [ ] | - [ ] |

---

## 2. Navigation Sidebar

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 2.1 | Click every nav item | Click each of the 11 nav items | Correct panel appears; clicked button highlighted; other buttons dimmed | - [ ] | - [ ] |
| 2.2 | Home returns to main view | Navigate to any panel, click Home | Output text area (or Short Session form) visible; no panel | - [ ] | - [ ] |
| 2.3 | Keyboard Up/Down arrows | Focus a nav button, press ↑ / ↓ | Focus moves to previous / next nav button | - [ ] | - [ ] |
| 2.4 | Keyboard Enter activates | Focus a nav button, press Enter | Panel opens, same as clicking | - [ ] | - [ ] |
| 2.5 | Arrow wraps at ends | Focus Home, press ↑ | Focus moves to About (wraps around) | - [ ] | - [ ] |

---

## 3. Home Panel — Control Bar & Output

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 3.1 | Mode toggle Regular → Short Session | Click "Short Session" segment | Short Session two-field form appears; output text area hidden | - [ ] | - [ ] |
| 3.2 | Mode toggle Short → Regular | Click "Regular" segment | Output text area appears; Short Session form hidden | - [ ] | - [ ] |
| 3.3 | Mode persists across restart | Set Short Session, close and reopen | App opens in Short Session mode | - [ ] | - [ ] |
| 3.4 | Start button label changes | Click Start | Button changes to "Stop"; status shows "Recording..." | - [ ] | - [ ] |
| 3.5 | Stop recording | Click Stop while recording | Button changes back to "Start" (then disabled briefly); status shows "Processing…" then "Done" | - [ ] | - [ ] |
| 3.6 | Signal meter moves | Click Start, speak or make noise | Signal meter bar animates | - [ ] | - [ ] |
| 3.7 | Signal meter resets after stop | Click Stop | Signal meter returns to zero | - [ ] | - [ ] |
| 3.8 | Output text right-click menu | Right-click inside output text area | Context menu: Select All, Copy | - [ ] | - [ ] |
| 3.9 | Ctrl+C copies selection | Select text in output, press Ctrl+C | Selected text on clipboard | - [ ] | - [ ] |
| 3.10 | Group selector dropdown | Click group dropdown in control bar | Available speaker groups listed | - [ ] | - [ ] |

---

## 4. Settings Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 4.1 | Panel opens | Click Settings | Settings panel visible with scrollable content | - [ ] | - [ ] |
| 4.2 | Mouse wheel scrolls | Hover over Settings content, scroll wheel | Content scrolls up/down smoothly | - [ ] | - [ ] |
| 4.3 | Language change | Change UI language dropdown (e.g. English → Russian) | All UI strings update immediately; nav buttons, labels, all panels in new language | - [ ] | - [ ] |
| 4.4 | Language persists | Change language, close and reopen | App opens in selected language | - [ ] | - [ ] |
| 4.5 | Input device dropdown | Open device dropdown | Lists available microphone/audio devices | - [ ] | - [ ] |
| 4.6 | Output folder browse | Click Browse next to output folder | File dialog opens; selected path appears in field | - [ ] | - [ ] |
| 4.7 | Settings auto-save | Change any setting, switch to another panel | Changing back to Settings shows the saved value | - [ ] | - [ ] |

---

## 5. Voice Profiles Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 5.1 | Panel opens | Click Voice Profiles | Groups list on left, Members list on right | - [ ] | - [ ] |
| 5.2 | Add Group | Click Add Group, enter name, confirm | New group appears in list | - [ ] | - [ ] |
| 5.3 | Rename Group | Select group, click Rename, enter new name | Group name updates in list | - [ ] | - [ ] |
| 5.4 | Delete Group | Select group, click Delete Group | Group removed; confirmation dialog shown first | - [ ] | - [ ] |
| 5.5 | Add Profile | Click Add Profile | Profile dialog opens with name fields | - [ ] | - [ ] |
| 5.6 | Edit Profile | Select a profile, click Edit | Profile dialog opens with existing data | - [ ] | - [ ] |
| 5.7 | Delete Profile | Select a profile, click Delete | Profile removed after confirmation | - [ ] | - [ ] |
| 5.8 | Import ZIP | Click Import ZIP, select a valid ZIP | Profiles imported; success message shown | - [ ] | - [ ] |
| 5.9 | Export ZIP | Click Export ZIP, choose save location | ZIP created at selected path; success message | - [ ] | - [ ] |
| 5.10 | Retrain All | Click Retrain All | Progress indicator shown; completes without error | - [ ] | - [ ] |

---

## 6. AI Config Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 6.1 | Panel opens | Click AI Config | Panel shows model and diarization settings | - [ ] | - [ ] |
| 6.2 | Whisper model dropdown | Open model dropdown | Shows: tiny, base, small, medium, large-v2, large-v3 | - [ ] | - [ ] |
| 6.3 | HuggingFace token field | Enter a token value | Field accepts text; saved to config | - [ ] | - [ ] |
| 6.4 | Settings persist | Change model, leave panel, return | Selected model still shown | - [ ] | - [ ] |

---

## 7. Substitution Dictionary Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 7.1 | Panel opens | Click Substitution Dictionary | Header row + scrollable content visible | - [ ] | - [ ] |
| 7.2 | Mouse wheel scrolls | Hover over dictionary rows, scroll wheel | Content scrolls smoothly | - [ ] | - [ ] |
| 7.3 | Add Row dialog opens | Click Add Row button | Dialog appears with two labeled input fields (Source, Replacement) | - [ ] | - [ ] |
| 7.4 | Add Row dialog — fields editable | In Add Row dialog, type in both fields | Text appears in fields | - [ ] | - [ ] |
| 7.5 | Add Row confirm | Fill fields, click Confirm | New row appears in dictionary list | - [ ] | - [ ] |
| 7.6 | Add Row cancel | Open dialog, click Cancel | Dialog closes; no row added | - [ ] | - [ ] |
| 7.7 | Add Row multiple times | Open and confirm dialog 3× | Each submission adds a new row without errors | - [ ] | - [ ] |
| 7.8 | Inline edit Source | Click in a Source cell and type | Text updates immediately | - [ ] | - [ ] |
| 7.9 | Inline edit Replacement | Click in a Replacement cell and type | Text updates immediately | - [ ] | - [ ] |
| 7.10 | Delete Row | Select a row, click Delete | Row removed from list | - [ ] | - [ ] |
| 7.11 | Undo | Add a row, click Undo | Row removed; previous state restored | - [ ] | - [ ] |
| 7.12 | Source help button | Click ? next to Source column | Help popup opens with explanation text | - [ ] | - [ ] |
| 7.13 | Replacement help button | Click ? next to Replacement column | Help popup opens with explanation text | - [ ] | - [ ] |
| 7.14 | Export CSV | Click Export CSV, choose save path | CSV file created at chosen location | - [ ] | - [ ] |
| 7.15 | Import CSV | Click Import CSV, select valid CSV | Rows added; import result message shown | - [ ] | - [ ] |
| 7.16 | Row right-click context menu | Right-click a Source or Replacement entry field | Context menu: Select All, Copy, Paste | - [ ] | - [ ] |

---

## 8. Batch Queue Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 8.1 | Panel opens | Click Batch Queue | File list (empty) + Add Files button visible | - [ ] | - [ ] |
| 8.2 | Add files | Click Add Files, select MP3/WAV | Files appear in list with status "Queued" | - [ ] | - [ ] |
| 8.3 | Remove file | Select file in list, click Remove | File removed from list | - [ ] | - [ ] |
| 8.4 | Clear queue | Click Clear All | All files removed | - [ ] | - [ ] |
| 8.5 | Queue progress bar | Add files, click Start Batch | Queue progress bar appears with N/M counter | - [ ] | - [ ] |

---

## 9. Output Config Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 9.1 | Panel opens | Click Output Config | Panel shows output format checkboxes and field toggles | - [ ] | - [ ] |
| 9.2 | Toggle output formats | Check/uncheck TXT, DOCX, SRT, JSON | Checkboxes respond; state saves to config | - [ ] | - [ ] |
| 9.3 | Toggle output fields | Check/uncheck Timestamp, Speaker, Text | Checkboxes respond; state saves | - [ ] | - [ ] |
| 9.4 | Translation toggle | Enable/disable translation | Setting saves; visible after panel revisit | - [ ] | - [ ] |

---

## 10. Hotkeys Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 10.1 | Panel opens | Click Hotkeys | Shows Start Recording and Stop Recording fields | - [ ] | - [ ] |
| 10.2 | Assign a hotkey | Click field, press a key combo (e.g. F9) | Key combo shown in field | - [ ] | - [ ] |
| 10.3 | Conflict detection | Set same key for Start and Stop | Warning or error shown | - [ ] | - [ ] |
| 10.4 | Clear hotkey | Click Clear next to a field | Field empties | - [ ] | - [ ] |
| 10.5 | Hotkey works (Windows) | Assign F9, minimize app, press F9 | Recording starts even with app in background | - [ ] | — |
| 10.6 | Hotkey works (Linux) | Assign F9, press F9 while app is focused | Recording starts | — | - [ ] |

---

## 11. Session History Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 11.1 | Panel opens | Click Session History | Table with columns: Date, Source, Duration, Speakers | - [ ] | - [ ] |
| 11.2 | Sessions listed | After completing a recording session | Session row appears in list | - [ ] | - [ ] |
| 11.3 | Select row | Click a session row | Row highlighted; row remains selected | - [ ] | - [ ] |
| 11.4 | Mouse wheel scrolls | Hover over session list, scroll wheel | List scrolls when content exceeds visible area | - [ ] | - [ ] |
| 11.5 | Mouse wheel on row label | Hover directly over a date/source label, scroll | List scrolls (event bubbles to canvas) | - [ ] | - [ ] |
| 11.6 | Delete Session | Select a session, click Delete Session | Row removed from list | - [ ] | - [ ] |
| 11.7 | Clear History | Click Clear History, confirm | All rows removed; empty state shown | - [ ] | - [ ] |
| 11.8 | Regenerate Output | Select a session, click Regenerate Output | Output files re-written; confirmation shown | - [ ] | - [ ] |

---

## 12. Backup & Restore Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 12.1 | Panel opens | Click Backup & Restore | Backup and Restore buttons visible | - [ ] | - [ ] |
| 12.2 | Create backup | Click Create Backup, choose path | ZIP file created; success message shown | - [ ] | - [ ] |
| 12.3 | Restore backup | Click Restore, select a valid ZIP | Data restored; app prompts to restart or reloads | - [ ] | - [ ] |
| 12.4 | Restore invalid file | Select a non-ZIP or wrong-format file | Error message shown; app data untouched | - [ ] | - [ ] |

---

## 13. About Panel

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 13.1 | Panel opens | Click About | Version, Author, and Build timestamp displayed | - [ ] | - [ ] |
| 13.2 | Version format | Read version field | Matches format `0.5.NNN` | - [ ] | - [ ] |

---

## 14. Short Session Mode

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 14.1 | Form visible in Short mode | Switch to Short Session, go to Home | Two text areas: Transcribed text + Translated text | - [ ] | - [ ] |
| 14.2 | Fields clear on Start | In Short mode, click Start | Both text areas clear | - [ ] | - [ ] |
| 14.3 | Translate and Save to Clipboard | After recording, click "Translate and save to clipboard" | Translated text copied to clipboard | - [ ] | - [ ] |
| 14.4 | Save to Clipboard | After recording, click "Save to clipboard" | Transcribed text copied to clipboard | - [ ] | - [ ] |

---

## 15. Mouse Wheel Scrolling (platform-specific)

| # | Test | Panel | Steps | Expected | Win | Lin |
|---|------|-------|-------|----------|-----|-----|
| 15.1 | Scroll Settings | Settings | Open panel, hover over content, scroll down | Content scrolls | - [ ] | - [ ] |
| 15.2 | Scroll Session History canvas | Session History | Hover over session rows, scroll down and up | Rows scroll | - [ ] | - [ ] |
| 15.3 | Scroll over row labels | Session History | Hover directly over a date text label, scroll | Canvas still scrolls (event captured) | - [ ] | - [ ] |
| 15.4 | Scroll Voice Profiles | Voice Profiles | Hover over members list, scroll | List scrolls | - [ ] | - [ ] |
| 15.5 | Scroll Output Config | Output Config | Hover over content, scroll | Content scrolls | - [ ] | - [ ] |

---

## 16. Window Behaviour

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 16.1 | Minimum window size | Drag window smaller than min | Window refuses to shrink below minimum (1127×620) | - [ ] | - [ ] |
| 16.2 | Resize reflows content | Resize window wider/taller | Panel content stretches to fill space | - [ ] | - [ ] |
| 16.3 | Close with X (default) | Click window X button | App closes; window geometry saved | - [ ] | - [ ] |
| 16.4 | Minimize to tray (Windows) | Enable "Minimize to tray" in Settings, click X | Window disappears; tray icon appears | - [ ] | — |
| 16.5 | Restore from tray (Windows) | Double-click tray icon | Window reappears | - [ ] | — |
| 16.6 | Tray right-click menu (Windows) | Right-click tray icon | Menu: Open, Start Recording, Stop Recording, Exit | - [ ] | — |
| 16.7 | Title bar recording indicator (Linux) | Start recording on Ubuntu | Window title shows "● Speech Recognition Program" | — | - [ ] |
| 16.8 | Title bar resets after stop (Linux) | Stop recording on Ubuntu | Bullet removed from title | — | - [ ] |

---

## 17. Context Menus & Clipboard

| # | Test | Widget | Steps | Expected | Win | Lin |
|---|------|--------|-------|----------|-----|-----|
| 17.1 | Right-click output text | Home output textbox | Right-click | Menu: Select All, Copy | - [ ] | - [ ] |
| 17.2 | Right-click dictionary entry | Dict Source/Replacement field | Right-click | Menu: Select All, Copy, Paste | - [ ] | - [ ] |
| 17.3 | Ctrl+A selects all | Any entry field | Click field, Ctrl+A | All text selected | - [ ] | - [ ] |
| 17.4 | Ctrl+C copies | Select text, Ctrl+C | Text on clipboard | - [ ] | - [ ] |
| 17.5 | Ctrl+V pastes | Click field, Ctrl+V | Clipboard text inserted | - [ ] | - [ ] |
| 17.6 | Ctrl+X cuts | Select text in editable field, Ctrl+X | Text removed, on clipboard | - [ ] | - [ ] |

---

## 18. Language Switching

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 18.1 | Switch to Russian | Settings → Language → Русский | All labels, buttons, nav items update to Russian | - [ ] | - [ ] |
| 18.2 | Switch back to English | Settings → Language → English | All labels revert to English | - [ ] | - [ ] |
| 18.3 | Panel content re-translates | Open Session History, change language | Column headers update immediately | - [ ] | - [ ] |
| 18.4 | Dictionary panel survives language change | Open Dictionary panel, change language | Dictionary rows and toolbar re-render correctly | - [ ] | - [ ] |

---

## 19. Error Handling

| # | Test | Steps | Expected | Win | Lin |
|---|------|-------|----------|-----|-----|
| 19.1 | No microphone | Remove/disable microphone, click Start | Error dialog appears with readable message | - [ ] | - [ ] |
| 19.2 | Import invalid CSV | Import CSV → Browse → select a TXT file | Error shown; no rows added | - [ ] | - [ ] |
| 19.3 | Restore invalid backup | Restore → select a random ZIP | Error shown; data unchanged | - [ ] | - [ ] |

---

## Test Run Log

| Date | Tester | Platform | Version | Notes |
|------|--------|----------|---------|-------|
|      |        | Windows  |         |       |
|      |        | Ubuntu   |         |       |

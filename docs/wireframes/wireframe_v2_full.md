# Wireframe V2 — Full-Featured Design

**Spec references:** 12.4, 12.6.d, 12.8  
**PDF file:** `wireframe_v2_full.pdf` (12 pages)

---

## Design Philosophy

A complete, production-quality desktop application that communicates capability and trustworthiness at first glance. Inspired by modern CustomTkinter showcase apps and contemporary web-to-desktop design trends (2025-2026). Key principles:

- **Card elevation**: related controls are grouped in visually distinct cards with subtle borders and background contrast.
- **Rich colour system**: a structured palette (slate-blue primary, emerald success, red danger, amber warning) communicates meaning consistently.
- **Rounded corners throughout**: `border-radius: ~3px` on all interactive elements gives a friendly, modern feel.
- **Information density with breathing room**: more content per screen than V1, but generous internal padding prevents crowding.
- **Coloured toolbar**: the navigation toolbar uses the primary blue, anchoring the visual hierarchy and making the app feel branded.
- **Typography scale**: clear size/weight distinctions between headings, body, and captions.

---

## Colour Palette

| Role | Hex | Usage |
|------|-----|-------|
| Page background | `#E8EDF5` | Outer page fill (slightly cool grey-blue) |
| Window / Card | `#FFFFFF` | Panel content cards |
| Title bar | `#1E3A5F` | Top chrome — deep navy |
| Toolbar / Nav | `#2563EB` | Navigation bar — rich blue |
| Sidebar bg | `#F0F4FA` | Settings/profile sidebar |
| Primary | `#2563EB` | Buttons, active states, links, progress fill |
| Primary text | `#FFFFFF` | Text on primary-coloured backgrounds |
| Secondary | `#64748B` | Secondary buttons text, labels, inactive elements |
| Accent / Danger | `#EF4444` | Record indicator, delete, errors |
| Success | `#10B981` | OK states, done indicators, save confirmations |
| Warning | `#F59E0B` | Outdated indicator, conflict warnings, advice |
| Text primary | `#1E293B` | Main body text — near-black slate |
| Text secondary | `#94A3B8` | Labels, placeholders, captions |
| Border | `#CBD5E1` | Card/element borders |
| Input background | `#F8FAFC` | Text fields, dropdowns |
| List item | `#F1F5F9` | Alternating row tint |
| List selected | `#DBEAFE` | Selected list item — light blue |
| Annotation | `#B91C1C` | Element callout circles in wireframe |

## Typography

| Role | Size | Weight | Family |
|------|------|--------|--------|
| Panel heading | 9.5 pt | Bold | Inter / Sans-serif |
| Body | 7.5 pt | Regular | Inter / Sans-serif |
| Small / caption | 6.2 pt | Regular | Inter / Sans-serif |
| Callout tags | 5.4 pt | Bold | Inter |
| Hotkey display | 7.5 pt | Regular | JetBrains Mono / Monospace |

## Geometry

- Corner radius: **~3 px** applied to buttons, input fields, cards, list items
- Border width: 0.5 px
- **Card shadows**: implied through border contrast (bg-card vs page bg)
- Button hover: primary colour lightens by ~10% (not shown in static wireframe)
- Focus rings: 2px primary-colour ring on focused inputs

---

## Page 1: Main Window — Regular Mode

The main window in this variant features a **coloured top toolbar** (primary blue) that contains device selection and mode controls, creating a strong branded header. The transcript area uses white cards with subtle borders for each segment cluster.

### Visual Enhancements over V1

- Coloured nav bar replaces plain grey toolbar
- Speaker names in primary blue, bolded
- Segment cards have a left-border accent in speaker colour
- Progress bars have gradient fill (blue → lighter blue) implied
- Recording indicator uses a pulsing animation (implied by red circle with white border)
- Mode toggle renders as pill-shaped button group

### Elements (shared with V1 — see V1 for full descriptions)

All element numbers match V1. Visual differences:

| # | Visual change |
|---|---------------|
| 1 | Device Dropdown: rounded corners, `#F8FAFC` fill, thicker border on focus |
| 2 | Signal Meter: bars have rounded tops; green → amber → red gradient colour coding |
| 3 | Recording Indicator: white border ring around the red circle creates a "halo" effect |
| 4 | Mode Toggle: pill-shaped button group; active option has full primary fill, inactive is ghost |
| 5 | Group Selector: placed in the blue nav bar (white text on blue) |
| 6–7 | Progress bars: rounded ends; gradient fill |
| 8 | Transcript area: each speaker block is a card with `3px` left-border accent in speaker colour |
| 9 | Play/Pause: rounded corners; icon-hint button |
| 10 | Seek slider: rounded track; handle has white fill + primary border |
| 11 | Timestamp: displayed in secondary colour, `font-variant-numeric: tabular-nums` |

---

## Page 2: Main Window — Short Session Mode (Amendment)

### Visual Enhancements

- Both text fields are white cards with blue focus rings when active
- Button 3 (Translate & Copy): primary fill, rounded, full-height on the right side of field 1
- Button 5 (Save to Clipboard): secondary (outline) button, matching height of field 2
- A thin horizontal card divider separates the two fields
- When translation is disabled: an animated slide-up removes field 2 and its button; field 1 card expands smoothly

### Elements

All element numbers and behaviours match V1 description. Additional design note:

**Field character count:** Both fields show a subtle character-count indicator in the bottom-right corner of each card (e.g., "247 chars"). This is cosmetic in the wireframe but will be implemented as a live counter.

---

## Page 3: Settings

### Visual Enhancements

The sidebar in this variant uses coloured category icons (implied by placeholder squares in wireframe). The active category has a primary-blue left-border accent and slightly brighter text. Form rows use alternating card backgrounds for scannability.

### Extended Element Documentation

| # | Visual detail | Additional behaviour |
|---|---------------|----------------------|
| 1 | Source Language | Searchable dropdown (type-ahead filtering) | Updates language label on next-run preview |
| 2 | Target Language | Paired with source; shows flag emoji next to name | Disabled when translation toggle is OFF |
| 3 | Whisper Model | Shows memory footprint estimate next to each option (e.g., "Medium — ~1.5 GB VRAM") | Warning badge if selected model not downloaded |
| 4 | Bad Audio Threshold | Live preview text below slider: "Segments with no_speech_prob > 0.60 will be flagged" | — |
| 5 | Min Profile Samples | Stepper control (+/−) beside text input | — |
| 6 | Translation Toggle | Switch is larger (taller) in V2 for easier click target | — |
| 7 | Auto-Start Toggle | Shows OS-specific note: "Writes to HKCU registry" | — |
| 8 | HuggingFace Licence | Shows a green checkmark badge if accepted; orange "not accepted" badge if not | — |
| 9 | Output Folder | Shows folder existence indicator (green dot = exists, red = missing) | — |

**Additional settings shown in this variant (Advanced section):**

| # | Name | Type | Description |
|---|------|------|-------------|
| 10 | Completion Sound | Dropdown | Audio file played when processing completes. Options: None, Chime (default), Beep. Files in `assets/sounds/`. |
| 11 | Translation Engine | Radio Group | Local (Helsinki-NLP OPUS-MT) vs Online (Google Translate). Online requires internet; Local is always available. |
| 12 | Display Language | Read-only label | "English (CLI and interface language is always English — Spec 15.2)" |

---

## Page 4: Voice Profile Management

### Visual Enhancements

- Three-column layout with visible card borders and a drop shadow on the detail pane
- Speaker list items show a coloured initial avatar (round coloured circle) left of the name
- "Drag speaker to group" guidance is shown as a highlighted info banner below the group list
- Speaker detail shows a larger avatar circle with initials
- Group membership tags in field 1 (Group 1) use a blue pill/badge style
- Import/Export buttons have icons (implied by text labels)

### Additional Elements (V2 only)

| # | Name | Type | Description |
|---|------|------|-------------|
| 12 | Sample Count Badge | Badge | Shows "N samples" below the avatar. Green if ≥ min threshold; amber if below. |
| 13 | Retrain Status | Status Label | Shows "Embeddings up to date" or "Retraining…" (spinner). Displayed in speaker detail when retraining is in progress. |

---

## Page 5: Substitution Dictionary

### Visual Enhancements

- Table header row uses primary-blue background with white text
- Alternating row colours are more pronounced
- Selected row has a blue left-border accent (3px)
- Source term cells use a slightly different font weight (medium) to distinguish from replacement cells
- Wildcard entries show a `*` badge in the Flags column using a coloured chip/pill

### Additional Elements (V2 only)

| # | Name | Description |
|---|------|-------------|
| 13 | Entry Count | Shows "N entries" in the top-right of the panel. Updates live as rows are added/deleted/filtered. |
| 14 | Case-Sensitive Toggle | Global toggle: when ON, all dictionary entries are case-sensitive. Default: OFF (case-insensitive). |

---

## Page 6: Batch Queue

### Visual Enhancements

- Queue rows have a progress bar that fills smoothly (animated in live app)
- "Processing" rows have a pulsing blue-left-border accent
- "Error" rows have a red-left-border accent and a "!" icon
- Right panel has card-separated action buttons with icons implied
- A summary row at the bottom: "Total: 5 files | 1h 26m | 3 completed, 1 in progress, 1 error"

### Additional Elements (V2 only)

| # | Name | Description |
|---|------|-------------|
| 10 | Queue Summary | Footer row below the file list. Shows total file count, estimated total duration, completion counts. Read-only. |
| 11 | Error Detail Button | Appears on "Error" rows. Opens a modal with the full error message and stack trace. |

---

## Page 7: Output Content Configuration

### Visual Enhancements

- Toggle switches are larger and colour-labelled (blue = enabled, grey = disabled)
- Format checkboxes replaced with card-style format selector: each format (TXT, DOCX, etc.) is a card that highlights when selected
- A live preview area shows a sample of what the output will look like with current settings

### Additional Elements (V2 only)

| # | Name | Description |
|---|------|-------------|
| 14 | Output Preview | Read-only text area showing a mock 2-segment output with the current field-toggle settings applied. Updates in real time as toggles change. |

---

## Page 8: Hotkey Configuration

### Visual Enhancements

- Each key-binding field renders as a bordered "key capsule" with keyboard-key styling
- Conflict fields turn amber with an animated shake on first focus
- A "Reset to Defaults" confirmation dialog is modal with clear Cancel / Confirm buttons
- Save button has a success checkmark animation on completion

---

## Page 9: Speaker Labelling Prompt

### Visual Enhancements

- Waveform rendered with filled gradient (blue fill below the zero-line)
- Start/End markers are draggable handles with tooltip showing time value
- Metadata form uses two-column layout for wider forms
- "Save Profile" button is full-width, primary, with save icon
- A confidence preview bar shows the estimated speaker match confidence based on the selected fragment length (longer = higher confidence)

### Additional Elements (V2 only)

| # | Name | Description |
|---|------|-------------|
| 15 | Fragment Confidence Preview | Horizontal indicator: "Confidence estimate: Good / Fair / Poor" based on fragment duration. < 5s = Poor, 5–10s = Fair, > 10s = Good. Read-only. |
| 16 | Speaker Suggestion | If pyannote finds a high-confidence match with an existing profile during labelling, shows "Possible match: Jane Doe (87%)" with an Accept / Ignore button. |

---

## Page 10: Session History

### Visual Enhancements

- Session list items use date headers (e.g., "Today", "Yesterday", "2026-05-17")
- "Outdated" sessions have an amber banner at the top of the detail pane
- Output file entries are clickable links with a file-type icon
- A "Copy Session JSON" button in the detail pane (for debugging)
- Regenerate Output shows a progress spinner during regeneration

### Additional Elements (V2 only)

| # | Name | Description |
|---|------|-------------|
| 13 | Date Group Headers | Non-interactive headers in the session list grouping sessions by day. |
| 14 | Copy JSON | Icon button in detail header. Copies the raw session JSON to clipboard for debugging. |
| 15 | Segment Preview | Expandable section in detail pane showing the first 3 transcribed segments as a preview. |

---

## Page 11: Backup and Restore

### Visual Enhancements

- Each section (Backup, Restore) is a card with a coloured header strip
- Backup section header: primary blue
- Restore section header: secondary slate
- Warning box uses amber fill with icon
- Progress bar shown during backup/restore operation (not shown in static wireframe)
- After successful backup: green success banner with file path and size

### Additional Elements (V2 only)

| # | Name | Description |
|---|------|-------------|
| 9 | Backup History List | A compact list of previous backups (file name, date, size) within the backup section. Each row has a "Restore from this" link. Populated by scanning the destination folder for `SRP_backup_*.zip` files. |

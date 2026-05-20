# Wireframe V3 — Dark Studio Design

**Spec references:** 12.4, 12.6.d, 12.8  
**PDF file:** `wireframe_v3_dark_studio.pdf` (12 pages)

---

## Design Philosophy

A professional audio workstation (DAW) aesthetic for users who spend long sessions transcribing and reviewing speech data. Inspired by Reaper, DaVinci Resolve, and modern dark-mode developer tools (VS Code, JetBrains IDEs).

Core principles:

- **Eyes come first.** Dark backgrounds reduce eye strain during extended sessions. The workspace is black; interactive elements distinguish themselves through colour and border, not surface.
- **Density without clutter.** Compact element sizes, tighter spacing, and monospace typography for data fields let more information fit on screen without visual crowding.
- **Signal over noise.** The teal/cyan primary accent is deliberately uncommon in the dark palette — it draws the eye to actionable elements without competing with data.
- **Recording is the hero action.** The recording indicator and signal meter are prominently sized. The user should always know at a glance whether the app is listening.
- **Professional trust cues.** The dark professional aesthetic signals that this is a serious tool — not a toy. It positions alongside pro software used by podcast editors, journalists, and researchers.

---

## Colour Palette

| Role | Hex | Usage |
|------|-----|-------|
| Page background | `#0D1117` | Outermost fill — near-black GitHub Dark |
| Window background | `#161B22` | Main window surface |
| Title bar | `#090D13` | Deeper than window — creates top chrome depth |
| Toolbar / Nav | `#1C2128` | Navigation strip |
| Panel / Card | `#21262D` | Raised card surfaces |
| Sidebar | `#161B22` | Left sidebars (same as window — no raised feel) |
| Primary / Action | `#00D4AA` | Teal-cyan: buttons, active states, progress fill, links |
| Primary text | `#0D1117` | Text on teal buttons — must be near-black for contrast |
| Secondary | `#8B949E` | Labels, captions, inactive element text |
| Accent / Danger | `#FF6B6B` | Recording indicator, delete, critical errors |
| Success | `#3FB950` | Done states, accepted licence |
| Warning | `#E3B341` | Outdated indicator, conflict warning, advice |
| Text primary | `#C9D1D9` | Body text — light grey, not pure white |
| Text secondary | `#6E7681` | Captions, placeholders |
| Border | `#30363D` | Element borders — subtle on dark bg |
| Input background | `#0D1117` | Text fields — same as page for minimal chrome |
| List item tint | `#21262D` | Alternating row bg |
| List selected | `#1F4C3A` | Dark green — complements teal primary |
| Annotation | `#FF6B6B` | Wireframe callout circles — high contrast on dark |

## Typography

| Role | Size | Weight | Family |
|------|------|--------|--------|
| Panel heading | 9.0 pt | Bold | Inter / Sans-serif |
| Body | 7.2 pt | Regular | Inter / Sans-serif |
| Small / caption | 6.0 pt | Regular | Inter / Sans-serif |
| Data fields | 7.2 pt | Regular | JetBrains Mono / Monospace |
| Hotkeys | 7.2 pt | Regular | JetBrains Mono |
| Callout tags | 5.2 pt | Bold | Inter |

Data values (timestamps, confidence scores, session IDs) use monospace font to preserve column alignment and reinforce the "technical data" register.

## Geometry

- Corner radius: **~1.5 px** — subtle rounding, not fully flat
- Border width: 0.7 px (slightly thicker than V2 — needed on dark bg for visibility)
- No external shadows (ineffective on dark backgrounds)
- Active states: border changes to primary teal (`#00D4AA`), ~1px thicker
- Focus rings: teal border glow implied

---

## Page 1: Main Window — Regular Mode

### Layout philosophy

The dark studio layout maximises the transcript area. Toolbars are compact. The signal meter is wider and more prominent (the audio feed is the app's core input). The recording indicator is larger and uses a steady bright-red glow — no subtle animation.

```
╔═ [0D1117] Title bar ════════════════════════ [●][─][✕] ═╗
║ Speech Recognition Program                               ║
╠═ [1C2128] Nav ════════════════════════════════════════════╣
║ ◀ Main Window — Regular Mode   [● REC]  [▐▐▐▐▐▐░░░░░░]  ║
╠═══════════════════════════════════════════════════════════╣
║ [Microphone (Realtek HD) ▾]    Group: [Group 1 ▾]        ║
║ Mode: [● Regular] [Short Session]                        ║
╠═══════════════════════════════════════════════════════════╣
║ File:  [▓▓▓▓▓░░░░░ 45%]    Queue: [▓░░░░░ 1/5 files]    ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  00:00:01,500  Speaker 1                                  ║
║  Hello, my name is John Smith. How are you today?        ║
║  ─────────────────────────────────────                   ║
║  00:00:06,000  Speaker 2                                  ║
║  I'm doing well. Let's discuss the agenda.               ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║ [▶]  [───────●────────────────]  01:23 / 05:47           ║
╚═══════════════════════════════════════════════════════════╝
```

### Unique design choices

- Signal meter is in the **nav bar** (right side), prominently visible — it's the most important real-time status indicator
- Recording indicator (REC) also lives in the nav bar — always visible regardless of scroll
- Segment layout: timestamp on its own line in monospace, then speaker name bolded in teal, then text on the next line. More compact but equally scannable
- No card borders around segments — dark background subtly separates them with alternating `#161B22` / `#21262D` row fills
- Playback controls are icon-only (`▶`, `⏸`, `⏭`) to save horizontal space

### Elements (same as V1 with dark visual treatment)

| # | Name | Dark Studio visual treatment |
|---|------|------------------------------|
| 1 | Device Dropdown | Dark `#0D1117` fill; teal border on focus |
| 2 | Signal Meter | Wide (12+ bars); positioned in nav bar; monochrome bars on idle, teal on active |
| 3 | Recording Indicator | Large bright `#FF6B6B` circle with text "REC" in white; steady (no animation in wireframe) |
| 4 | Mode Toggle | Compact pill; active = teal fill + dark text; inactive = outline only |
| 5 | Group Selector | In main toolbar row; same dark treatment as device dropdown |
| 6–7 | Progress bars | Teal fill; `#0D1117` track; monospace percentage text |
| 8 | Transcript area | Alternating dark row fills; timestamps in monospace secondary colour; speaker names in teal bold; text in primary light grey |
| 9 | Play button | Ghost button (teal border, no fill); icon-only |
| 10 | Seek slider | Dark track; teal fill for played portion; teal circle handle |
| 11 | Timestamp | Monospace, secondary colour |

---

## Page 2: Main Window — Short Session Mode (Amendment)

### Unique design choices

- Both text fields are `#0D1117` (same as page background) — the text area literally disappears into the page, emphasising the text content over the container
- Field borders are single-pixel teal when the field has focus
- "Translate & Copy" button spans the full height of field 1's row on the right side
- A thin `#30363D` horizontal rule separates the two field sections
- When translation is disabled: field 2 collapses with a smooth height animation; the horizontal rule disappears

### Field character counts

Both fields show character count in monospace secondary colour at the bottom-right of each field: `247 chars`.

---

## Page 3: Settings

### Unique design choices

- Sidebar uses no raised surface — it blends with the window background (`#161B22`)
- Active sidebar item: teal left-border accent (3px) + teal text
- Form rows use no alternating colours — clean uniform dark surface
- Toggles are the most prominent elements (teal when ON)
- Slider track is `#0D1117` (recessed); handle is teal circle
- All input fields have `#0D1117` fill — they look "cut into" the surface

### Extended Element Documentation

| # | Dark Studio specific | Behaviour |
|---|----------------------|-----------|
| 1 | Source Language Dropdown | Monospace value display; filtered by type-ahead | |
| 3 | Whisper Model | Shows "VRAM: ~1.5 GB" next to each option in secondary colour | Amber badge if model not downloaded |
| 4 | Bad Audio Threshold | Slider fill in teal; threshold value in monospace next to handle | — |
| 8 | HuggingFace Licence | Red border + red text "DISABLED — diarization inactive" when not accepted; green border + green text when accepted | — |

**Additional Dark Studio settings (Advanced section):**

| # | Name | Type | Description |
|---|------|------|-------------|
| 10 | GPU / CPU selector | Toggle | Force CPU even when CUDA available. For machines that share GPU with gaming. |
| 11 | Transcript Font Size | Slider | Adjusts the font size in the main transcript area. Range: 8–20pt. |
| 12 | Waveform Colour | Colour Picker | Teal by default; user can customise the waveform/meter accent colour. Persisted in config. |

---

## Page 4: Voice Profile Management

### Unique design choices

- Speaker list: compact rows (3.5 units tall vs 4.5 in V1/V2); shows initial avatar + name + sample count
- Group list: borderless, blends into sidebar
- Speaker detail: large avatar replaced with a waveform thumbnail (1-second excerpt from most recent sample) drawn in teal on dark background
- Metadata fields use monospace font — emphasises the "data record" nature
- Drag-to-group: shown as a dashed teal border on the group list item when hovering with a dragged speaker

### Group membership display

Group membership is shown as teal pill badges at the bottom of the detail panel. Clicking a badge opens a confirmation to remove from group.

---

## Page 5: Substitution Dictionary

### Unique design choices

- Table header: dark `#21262D` with secondary-colour text (no primary-colour header)
- Selected row: `#1F4C3A` (dark green) — matches the list-selected colour
- Source term column uses a slightly lighter grey to distinguish from replacement
- Wildcard asterisks (`*`) in source terms are highlighted in teal
- The search field uses `#0D1117` fill with a teal left-border when focused

### Monospace convention

Source terms, replacements, and flags are displayed in monospace font — these are "data patterns" and monospace improves readability of special characters (`*`, `.`, `/`).

---

## Page 6: Batch Queue

### Unique design choices

- Queue rows use monospace font for duration and file names
- "Processing" rows have an animated teal-left-border pulse (implied in wireframe)
- Progress bar uses teal fill on `#0D1117` track
- Error rows have `#FF6B6B` left-border accent
- Right panel shows a compact ASCII-style queue summary at the top:
  ```
  QUEUE: 5 files  |  01:26:14 total
  Done: 3  Processing: 1  Error: 1
  ```

---

## Page 7: Output Content Configuration

### Unique design choices

- Toggles on dark bg: the switch track is clearly visible as `#30363D`; when ON, the track is teal
- Format selection uses monospace extension labels: `.txt`, `.docx`, `.srt`, `.json`
- Checkboxes are square with teal fill when checked
- Output folder field uses monospace font (it's a file path — a data value)

---

## Page 8: Hotkey Configuration

### Unique design choices

- Key capture fields render as "terminal-style" key capsules: dark `#0D1117` fill, `#30363D` border, `1px` top-highlight (`#3D444B`) to simulate key depth
- Active/focused key field: teal border
- Conflict indicator: amber `⚠` icon + amber border on the conflicting field
- The action list is more compact (5 units row height vs 6.5 in V1)
- Save/Reset buttons use full-width layout in the footer of the panel

### Keyboard Shortcut Philosophy (V3 only)

This variant recommends Vim-style or media-key-heavy shortcuts because target users are assumed to have both hands on the keyboard during sessions. The default suggestion set leans toward Fn-keys and simple Ctrl combinations rather than three-key chords.

---

## Page 9: Speaker Labelling Prompt

### Unique design choices

- Waveform rendered with **teal fill below the zero line** on `#0D1117` background — looks like a proper audio editor waveform
- Start/End markers are teal vertical lines with triangular handles
- Playback controls are minimal icon buttons (no text labels)
- Metadata form is two-column, compact, monospace values
- The "Save Profile" button is teal-filled (high contrast on dark bg)
- The confidence estimate (fragment length vs quality) is shown as a single-line status: "Fragment: 10.0s — Good confidence"

### Waveform interaction detail

The waveform display area supports mouse-drag to reposition start/end markers directly on the waveform. This is more natural than separate slider controls and aligns with DAW/audio editor conventions.

### Additional V3-only element

| # | Name | Description |
|---|------|-------------|
| 15 | Speaker Name Preview | Below the save button: shows the folder name that will be created (e.g., `Smith_John`) derived from the current field values. Updates in real time. Monospace font, secondary colour. |

---

## Page 10: Session History

### Unique design choices

- Session list uses a very compact format: date in monospace, source type as a coloured badge (`[FILE]` in teal, `[MIC]` in orange, `[BATCH]` in blue), duration in monospace
- The detail pane renders all values in monospace — emphasises machine-readable data
- Output file paths are shown in monospace and are truncated with ellipsis in the middle: `C:\Users\Leo1\...\interview_WSP.txt`
- "Regenerate Output" is a teal outlined button (ghost style)
- "Delete Session" is a red outlined button

### Session JSON preview (V3 only)

The detail pane includes a collapsible raw JSON preview showing the full session JSON (first 10 lines, then "▼ Show more"). Uses monospace font. For developers/power users who want to inspect or copy the raw data.

---

## Page 11: Backup and Restore

### Unique design choices

- Both sections are side-by-side within the window — no separate card boxes; the visual separation comes from a single vertical `#30363D` divider
- Warning box uses `#E3B341` text and border on dark background (no yellow fill — fills look washed-out on dark)
- All file path fields are monospace
- The restore section includes a compact "last 3 backups" list in the same column, below the file picker — user can restore from a recent backup without browsing

### Backup progress (V3 only)

When a backup is in progress, the "Create Backup Now" button is replaced by a progress bar showing "Backing up voice profiles… (2/5 speakers)" in monospace. The right section shows the estimated completion time.

---

## Summary: Design Comparison

| Dimension | V1 Minimalist | V2 Full-Featured | V3 Dark Studio |
|-----------|--------------|------------------|----------------|
| Target user | General users, low-distraction preference | Users who prefer rich UI and visual feedback | Power users, long sessions, pro context |
| Primary colour area | White page + blue accents | Blue nav bars + white cards | Black page + teal accents |
| Corner radius | 0 (flat) | 3 px (modern) | 1.5 px (subtle) |
| Typography density | Comfortable spacing | Comfortable spacing | Compact/dense |
| Monospace usage | Timestamps, hotkeys | Timestamps, hotkeys | Timestamps, hotkeys, all data fields |
| Progress/status | Simple bars | Gradient bars with icons | Dark track, teal fill |
| Segment display | Speaker name + range + text | Speaker card with left-border | Timestamp + name + text, alternating rows |
| Key differentiator | Maximum content focus | Visual richness and guidance | Professional/technical credibility |

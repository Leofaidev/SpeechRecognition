#!/usr/bin/env bash
# WSP Ubuntu check suite — runs automated checks and prints manual check instructions.
#
# Usage (from repo root):
#   bash scripts/check_ubuntu.sh
#
# Requires: venv already set up by scripts/setup-ubuntu.sh

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$REPO/.venv-linux"
PYTHON="$VENV/bin/python3"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0

pass() { echo -e "${GREEN}  PASS${NC}  $1"; ((PASS++)); }
fail() { echo -e "${RED}  FAIL${NC}  $1"; ((FAIL++)); }
skip() { echo -e "${YELLOW}  SKIP${NC}  $1"; ((SKIP++)); }
header() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }

# ---------------------------------------------------------------------------
header "CHK-U01  Python version"
# ---------------------------------------------------------------------------
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 11 ]]; then
    pass "Python $PY_VER (≥ 3.11)"
else
    fail "Python $PY_VER — need 3.11+"
fi

# ---------------------------------------------------------------------------
header "CHK-U02  Key imports"
# ---------------------------------------------------------------------------
IMPORTS=(faster_whisper customtkinter pyaudio cv2 keyboard)
for mod in "${IMPORTS[@]}"; do
    if "$PYTHON" -c "import $mod" 2>/dev/null; then
        pass "import $mod"
    else
        fail "import $mod"
    fi
done
# pyannote is large — just check the package is importable, not that models load
if "$PYTHON" -c "import pyannote.audio" 2>/dev/null; then
    pass "import pyannote.audio"
else
    fail "import pyannote.audio"
fi

# ---------------------------------------------------------------------------
header "CHK-U03  Unit tests"
# ---------------------------------------------------------------------------
cd "$REPO"
TEST_OUT=$("$VENV/bin/pytest" tests/unit/ -q --tb=no 2>&1 | tail -3)
if echo "$TEST_OUT" | grep -q "passed" && ! echo "$TEST_OUT" | grep -q "error"; then
    pass "pytest tests/unit/  — $TEST_OUT"
else
    fail "pytest tests/unit/  — $TEST_OUT"
fi

# ---------------------------------------------------------------------------
header "CHK-U04  CLI — file processing (TXT output)"
# ---------------------------------------------------------------------------
FIXTURE="$REPO/tests/fixtures/english_10s.wav"
OUT_DIR="$TMP/out_txt"
mkdir -p "$OUT_DIR"
PYTHONPATH="$REPO/src:$REPO/platforms" "$PYTHON" -m cli.parser \
    --input "$FIXTURE" --output "$OUT_DIR" --format txt \
    > "$TMP/cli_txt.log" 2>&1
CLI_EXIT=$?
if [[ $CLI_EXIT -eq 0 ]] && ls "$OUT_DIR"/*.txt &>/dev/null; then
    pass "CLI exit 0; TXT file created ($(wc -c < "$(ls "$OUT_DIR"/*.txt | head -1)") bytes)"
else
    fail "CLI exited $CLI_EXIT — $(cat "$TMP/cli_txt.log" | tail -3)"
fi

# ---------------------------------------------------------------------------
header "CHK-U05  CLI — SRT and DOCX output formats"
# ---------------------------------------------------------------------------
for fmt in srt docx; do
    OUT_DIR_FMT="$TMP/out_$fmt"
    mkdir -p "$OUT_DIR_FMT"
    PYTHONPATH="$REPO/src:$REPO/platforms" "$PYTHON" -m cli.parser \
        --input "$FIXTURE" --output "$OUT_DIR_FMT" --format "$fmt" \
        > "$TMP/cli_$fmt.log" 2>&1
    EXIT=$?
    if [[ $EXIT -eq 0 ]] && ls "$OUT_DIR_FMT"/*."$fmt" &>/dev/null; then
        pass "CLI --format $fmt → file created"
    else
        fail "CLI --format $fmt exited $EXIT — $(cat "$TMP/cli_$fmt.log" | tail -2)"
    fi
done

# ---------------------------------------------------------------------------
header "CHK-U06  Translation (OPUS-MT local)"
# ---------------------------------------------------------------------------
TRANS_OUT=$("$PYTHON" - <<'PYEOF' 2>&1
import sys
sys.path.insert(0, '/home/claude/SpeechRecognition/src')
from translation.opus_mt import OpusMTTranslator
t = OpusMTTranslator('en', 'de')
result = t.translate(['Hello world'])
assert result and result[0] and result[0] != 'Hello world', f"Unexpected: {result}"
print(f"OK: 'Hello world' -> '{result[0]}'")
PYEOF
)
TRANS_EXIT=$?
if [[ $TRANS_EXIT -eq 0 ]]; then
    pass "OPUS-MT en→de: $TRANS_OUT"
else
    fail "OPUS-MT translation failed: $TRANS_OUT"
fi

# ---------------------------------------------------------------------------
header "CHK-U07  Backup — creates ZIP"
# ---------------------------------------------------------------------------
BACKUP_DIR="$TMP/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_OUT=$("$PYTHON" - <<PYEOF 2>&1
import sys
sys.path.insert(0, '$REPO/src')
sys.path.insert(0, '$REPO/platforms')
from backup.manager import BackupManager
from pathlib import Path
mgr = BackupManager(
    library_root=Path('$REPO/library'),
    sessions_dir=Path('$REPO/sessions'),
    dictionary_file=Path('$REPO/dictionary.json'),
    config_file=Path('$REPO/config.json'),
    backup_dir=Path('$BACKUP_DIR'),
)
p = mgr.create()
assert p.exists() and p.suffix == '.zip', f"Bad backup path: {p}"
print(f"OK: {p.name} ({p.stat().st_size} bytes)")
PYEOF
)
BACKUP_EXIT=$?
if [[ $BACKUP_EXIT -eq 0 ]]; then
    pass "Backup ZIP created: $BACKUP_OUT"
else
    fail "Backup failed: $BACKUP_OUT"
fi

# ---------------------------------------------------------------------------
header "CHK-U08  Restore — ZIP restores cleanly"
# ---------------------------------------------------------------------------
RESTORE_OUT=$("$PYTHON" - <<PYEOF 2>&1
import sys, glob
sys.path.insert(0, '$REPO/src')
sys.path.insert(0, '$REPO/platforms')
from backup.restorer import BackupRestorer
from pathlib import Path
zips = sorted(Path('$BACKUP_DIR').glob('*.zip'))
assert zips, 'No backup ZIP found'
r = BackupRestorer(
    restore_dir=Path('$TMP/restore_target'),
)
r.restore(zips[-1])
print(f"OK: restored from {zips[-1].name}")
PYEOF
)
RESTORE_EXIT=$?
if [[ $RESTORE_EXIT -eq 0 ]]; then
    pass "Restore succeeded: $RESTORE_OUT"
else
    fail "Restore failed: $RESTORE_OUT"
fi

# ---------------------------------------------------------------------------
header "CHK-U09  GUI headless launch (Xvfb)"
# ---------------------------------------------------------------------------
if ! command -v Xvfb &>/dev/null; then
    skip "Xvfb not installed — install with: sudo apt install xvfb"
else
    DISPLAY_NUM=99
    Xvfb ":$DISPLAY_NUM" -screen 0 1280x800x24 &>/dev/null &
    XVFB_PID=$!
    sleep 1
    DISPLAY=":$DISPLAY_NUM" PYTHONPATH="$REPO/src:$REPO/platforms" \
        "$PYTHON" -m gui.app &>/dev/null &
    GUI_PID=$!
    sleep 5
    if kill -0 "$GUI_PID" 2>/dev/null; then
        pass "GUI process running after 5s (PID $GUI_PID)"
        kill "$GUI_PID" 2>/dev/null || true
    else
        fail "GUI process exited within 5s — check logs"
    fi
    kill "$XVFB_PID" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
header "CHK-U10  Auto-start (XDG autostart entry)"
# ---------------------------------------------------------------------------
AUTOSTART_OUT=$("$PYTHON" - <<PYEOF 2>&1
import sys
sys.path.insert(0, '$REPO/src')
sys.path.insert(0, '$REPO/platforms')
from platforms.linux.auto_start import AutoStart
a = AutoStart()
a.enable('/usr/bin/python3')
assert a.is_enabled(), 'enable() did not set entry'
a.disable()
assert not a.is_enabled(), 'disable() did not remove entry'
print('OK: enable/disable XDG autostart entry')
PYEOF
)
AUTOSTART_EXIT=$?
if [[ $AUTOSTART_EXIT -eq 0 ]]; then
    pass "Auto-start: $AUTOSTART_OUT"
else
    fail "Auto-start: $AUTOSTART_OUT"
fi

# ---------------------------------------------------------------------------
header "MANUAL CHECKS (run with the GUI open on the desktop)"
# ---------------------------------------------------------------------------
echo ""
echo "  CHK-U11  Open the app (bash run-linux.sh) and verify all 9 sidebar panels"
echo "           render without errors: Settings, Voice Profiles, AI Config,"
echo "           Substitution Dictionary, Batch Queue, Output Config, Hotkeys,"
echo "           Session History, Backup & Restore."
echo ""
echo "  CHK-U12  Switch to the Home panel, select a microphone from the Input Device"
echo "           dropdown, click Start, speak for 5 seconds, click Stop."
echo "           Verify a TXT file is created in the output folder."
echo ""
echo "  CHK-U13  Minimise the app. Press the configured hotkey (default F12)."
echo "           Verify the recording indicator appears in the window title."
echo "           (Requires user to be in the 'input' group: sudo usermod -aG input \$USER)"
echo ""
echo "  CHK-U14  Verify the system tray icon appears in the notification area."
echo "           Right-click it and confirm the menu items are present."
echo ""

# ---------------------------------------------------------------------------
header "Summary"
# ---------------------------------------------------------------------------
TOTAL=$((PASS + FAIL + SKIP))
echo ""
echo -e "  Results: ${GREEN}$PASS PASS${NC}  ${RED}$FAIL FAIL${NC}  ${YELLOW}$SKIP SKIP${NC}  (of $TOTAL automated)"
echo ""
if [[ $FAIL -eq 0 ]]; then
    echo -e "  ${GREEN}All automated checks passed.${NC} Complete the 4 manual checks above."
    exit 0
else
    echo -e "  ${RED}$FAIL automated check(s) failed.${NC} Fix before running manual checks."
    exit 1
fi

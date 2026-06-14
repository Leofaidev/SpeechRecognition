#!/bin/bash
# Automated UI test navigator for WSP app on Ubuntu
# Takes a screenshot after each navigation action and saves to /tmp/wsp_test_NNN.png

XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0
export XAUTHORITY=$XAUTH

SCR_DIR="/tmp/wsp_screens"
mkdir -p "$SCR_DIR"

_ss() {
  # $1 = label  $2 = number
  import -window root "$SCR_DIR/$(printf '%03d' $2)_${1}.png" 2>/dev/null \
    || scrot "$SCR_DIR/$(printf '%03d' $2)_${1}.png" 2>/dev/null \
    || true
}

_click() { xdotool mousemove $1 $2 click 1; sleep 0.5; }
_dclick(){ xdotool mousemove $1 $2 click --repeat 2 1; sleep 0.5; }
_scroll_down(){ xdotool mousemove $1 $2; for i in 1 2 3 4 5; do xdotool click 5; sleep 0.08; done; }
_scroll_up()  { xdotool mousemove $1 $2; for i in 1 2 3 4 5; do xdotool click 4; sleep 0.08; done; }
_type()  { xdotool type --clearmodifiers "$1"; sleep 0.3; }
_key()   { xdotool key "$1"; sleep 0.3; }

# Nav y-coordinates (actual 1280x800 pixels)
NAV_X=150
Y_HOME=134
Y_SETTINGS=172
Y_PROFILES=210
Y_AI=248
Y_DICT=286
Y_BATCH=324
Y_OUTPUT=362
Y_HOTKEYS=400
Y_HISTORY=438
Y_BACKUP=476
Y_ABOUT=514

N=1

# ---- 1. Launch state -------------------------------------------------------
echo "=== 1. Launch state"
_ss "01_launch_home" $N; N=$((N+1))

# ---- 2. Navigation: click each nav item ------------------------------------
echo "=== 2. Navigation"
_click $NAV_X $Y_SETTINGS; sleep 0.5
_ss "02_nav_settings" $N; N=$((N+1))

_click $NAV_X $Y_PROFILES; sleep 0.5
_ss "02_nav_profiles" $N; N=$((N+1))

_click $NAV_X $Y_AI; sleep 0.5
_ss "02_nav_ai_config" $N; N=$((N+1))

_click $NAV_X $Y_DICT; sleep 0.5
_ss "02_nav_dict" $N; N=$((N+1))

_click $NAV_X $Y_BATCH; sleep 0.5
_ss "02_nav_batch" $N; N=$((N+1))

_click $NAV_X $Y_OUTPUT; sleep 0.5
_ss "02_nav_output" $N; N=$((N+1))

_click $NAV_X $Y_HOTKEYS; sleep 0.5
_ss "02_nav_hotkeys" $N; N=$((N+1))

_click $NAV_X $Y_HISTORY; sleep 0.5
_ss "02_nav_history" $N; N=$((N+1))

_click $NAV_X $Y_BACKUP; sleep 0.5
_ss "02_nav_backup" $N; N=$((N+1))

_click $NAV_X $Y_ABOUT; sleep 0.5
_ss "02_nav_about" $N; N=$((N+1))

_click $NAV_X $Y_HOME; sleep 0.5
_ss "02_nav_home_return" $N; N=$((N+1))

# ---- 3. Home panel ---------------------------------------------------------
echo "=== 3. Home"
# 3.1 mode toggle: switch to Regular
_click 293 44; sleep 0.5   # "Regular" segment button
_ss "03_mode_regular" $N; N=$((N+1))

# 3.1 switch to Short Session
_click 330 44; sleep 0.5   # "Short Session" segment button
_ss "03_mode_short" $N; N=$((N+1))

# Switch back to Regular for remaining tests
_click 293 44; sleep 0.5

# 3.4 Start recording — verify button label changes
_click 381 44; sleep 1.0   # Start button
_ss "03_recording_start" $N; N=$((N+1))

# 3.5 Stop recording
_click 381 44; sleep 2.0   # Stop button (same position)
_ss "03_recording_stop" $N; N=$((N+1))

# ---- 4. Settings -----------------------------------------------------------
echo "=== 4. Settings"
_click $NAV_X $Y_SETTINGS; sleep 0.5
_ss "04_settings_open" $N; N=$((N+1))

# 4.2 Mouse wheel scroll
_scroll_down 640 300
_ss "04_settings_scroll_down" $N; N=$((N+1))
_scroll_up 640 300
_ss "04_settings_scroll_up" $N; N=$((N+1))

# ---- 5. Voice Profiles -----------------------------------------------------
echo "=== 5. Voice Profiles"
_click $NAV_X $Y_PROFILES; sleep 0.5
_ss "05_profiles_open" $N; N=$((N+1))

# ---- 6. AI Config ----------------------------------------------------------
echo "=== 6. AI Config"
_click $NAV_X $Y_AI; sleep 0.5
_ss "06_ai_config_open" $N; N=$((N+1))

# ---- 7. Substitution Dictionary --------------------------------------------
echo "=== 7. Dictionary"
_click $NAV_X $Y_DICT; sleep 0.5
_ss "07_dict_open" $N; N=$((N+1))

# 7.2 Mouse wheel scroll (may be short list)
_scroll_down 640 300

# 7.3 Add Row dialog — click Add Row button (approx x=340, y=162 actual)
_click 340 162; sleep 0.8
_ss "07_dict_add_row_dialog" $N; N=$((N+1))

# 7.4 Type in Source field (dialog should have focus)
_type "testword"; sleep 0.3
_key "Tab"
_type "replacement"; sleep 0.3
_ss "07_dict_add_row_filled" $N; N=$((N+1))

# 7.5 Confirm
_key "Return"; sleep 0.5
_ss "07_dict_after_add" $N; N=$((N+1))

# 7.7 Add Row again (second time — regression for blank dialog bug)
_click 340 162; sleep 0.8
_ss "07_dict_add_row_second" $N; N=$((N+1))
_key "Escape"; sleep 0.3

# 7.12 Source help button
_click 460 132; sleep 0.5   # ? button near Source header
_ss "07_dict_help_source" $N; N=$((N+1))
_key "Escape"; sleep 0.3

# ---- 8. Batch Queue --------------------------------------------------------
echo "=== 8. Batch Queue"
_click $NAV_X $Y_BATCH; sleep 0.5
_ss "08_batch_open" $N; N=$((N+1))

# ---- 9. Output Config -------------------------------------------------------
echo "=== 9. Output Config"
_click $NAV_X $Y_OUTPUT; sleep 0.5
_ss "09_output_open" $N; N=$((N+1))

# ---- 10. Hotkeys ------------------------------------------------------------
echo "=== 10. Hotkeys"
_click $NAV_X $Y_HOTKEYS; sleep 0.5
_ss "10_hotkeys_open" $N; N=$((N+1))

# ---- 11. Session History ----------------------------------------------------
echo "=== 11. Session History"
_click $NAV_X $Y_HISTORY; sleep 0.5
_ss "11_history_open" $N; N=$((N+1))

# 11.4 Mouse wheel scroll
_scroll_down 640 300
_ss "11_history_scroll_down" $N; N=$((N+1))
_scroll_up 640 300
_ss "11_history_scroll_up" $N; N=$((N+1))

# 11.3 Select a row (click first data row)
_click 400 130; sleep 0.3
_ss "11_history_row_selected" $N; N=$((N+1))

# ---- 12. Backup & Restore ---------------------------------------------------
echo "=== 12. Backup & Restore"
_click $NAV_X $Y_BACKUP; sleep 0.5
_ss "12_backup_open" $N; N=$((N+1))

# ---- 13. About --------------------------------------------------------------
echo "=== 13. About"
_click $NAV_X $Y_ABOUT; sleep 0.5
_ss "13_about_open" $N; N=$((N+1))

# ---- 14. Short Session mode -------------------------------------------------
echo "=== 14. Short Session"
_click $NAV_X $Y_HOME; sleep 0.5
_click 330 44; sleep 0.5   # Short Session segment
_ss "14_short_session_form" $N; N=$((N+1))

# ---- 17. Right-click context menu -------------------------------------------
echo "=== 17. Context menu"
_click $NAV_X $Y_HOME; sleep 0.3
_click 293 44; sleep 0.3   # back to Regular
_click 350 44; sleep 0.3   # wait — click somewhere in output area
# Right-click output textbox area
xdotool mousemove 640 180
xdotool click 3; sleep 0.5
_ss "17_context_menu_output" $N; N=$((N+1))
_key "Escape"; sleep 0.3

# ---- 18. Language switch ----------------------------------------------------
echo "=== 18. Language switch"
_click $NAV_X $Y_SETTINGS; sleep 0.5
# Scroll to top first
_scroll_up 640 300
_ss "18_settings_before_lang" $N; N=$((N+1))

echo "=== DONE ==="
echo "Screenshots in $SCR_DIR"
ls -la "$SCR_DIR"/*.png | wc -l

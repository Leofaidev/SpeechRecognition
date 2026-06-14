#!/bin/bash
XAUTH=$(ls /run/user/1001/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DISPLAY=:0
export XAUTHORITY=$XAUTH

_click()  { xdotool mousemove $1 $2 click 1; sleep ${3:-0.5}; }
_rclick() { xdotool mousemove $1 $2 click 3; sleep ${3:-0.5}; }
_scroll_up() { xdotool mousemove $1 $2; for i in 1 2 3 4 5 6 8; do xdotool click 4; sleep 0.07; done; }
_type() { xdotool type --clearmodifiers "$1"; sleep 0.3; }
_key()  { xdotool key "$1"; sleep 0.3; }

NAV=150
Y_SET=172; Y_DICT=286; Y_HOT=400; Y_HIST=438

case $1 in

# 18. Language switch: open dropdown in Settings
lang_open_dropdown)
    _click $NAV $Y_SET 0.6
    _scroll_up 700 300
    sleep 0.3
    # Language dropdown actual coords: ~464, 330
    _click 464 330 0.8
    ;;

# Click the 'ru' option in the opened dropdown (position varies)
lang_pick_ru)
    # After dropdown opens, options appear below.
    # 'ru' should appear just below the dropdown — roughly y=360 actual
    _click 464 360 0.8
    ;;

# Language back to English
lang_pick_en)
    _click $NAV $Y_SET 0.6
    _scroll_up 700 300
    sleep 0.3
    _click 464 330 0.8
    sleep 0.5
    _click 464 346 0.8   # 'en' is first option
    ;;

# 7. Add Row then use mouse click into Replacement field (workaround for Tab)
dict_add_row_mouse)
    _click $NAV $Y_DICT 0.5
    _click 340 162 1.0   # Add Row button
    sleep 0.8
    # Source entry: approx x=680, y=242 actual (center of Source field in dialog)
    _click 680 242 0.4
    _type "tabtest"
    # Click Replacement entry directly: approx x=680, y=278 actual
    _click 680 278 0.4
    _type "tabresult"
    # Click Confirm: approx x=746, 322 actual
    _click 746 322 0.6
    ;;

# 10. Hotkeys: clear one field, set different key, verify no conflict
hotkey_set_f11)
    _click $NAV $Y_HOT 0.6
    # Click Stop Recording field (approx x=860, y=246 actual)
    _click 860 246 0.4
    # Select all and delete
    _key ctrl+a
    _key Delete
    sleep 0.3
    # Press F11
    _key F11
    sleep 0.3
    # Save
    _click 1104 290 0.4   # Save button approx
    ;;

# 2. Sidebar keyboard navigation test
sidebar_focus_home)
    # Click Home nav button to focus it
    _click $NAV 134 0.4
    # Now press Down twice (should move to Settings then Voice Profiles)
    xdotool key Down
    sleep 0.4
    xdotool key Down
    sleep 0.4
    # Press Return to activate (should open Voice Profiles)
    xdotool key Return
    sleep 0.6
    ;;

esac

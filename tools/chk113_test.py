"""CHK-113 automated verification: ctrl+c conflict warning shows orange."""
import sys, os, subprocess, tempfile, json, time

sys.path.insert(0, r"H:\Users\Leo1\SpeechRecognition\src")

import customtkinter as ctk
from gui.panels.hotkeys_panel import HotkeysPanel
from config.store import ConfigStore

def t(k, **kw):
    templates = {
        "hotkeys_title": "Hotkey Configuration",
        "hotkey_start_label": "Start Recording",
        "hotkey_stop_label": "Stop Recording",
        "btn_reset_hotkeys": "Reset to Defaults",
        "btn_save_hotkeys": "Save",
        "hotkey_conflict_warning": "'{key}' conflicts: {reason}",
        "hotkey_system_conflict": "'{key}' is registered by another app.",
        "hotkey_ctrl_alt_blocked": "Ctrl+Alt combinations are not allowed.",
        "hotkey_system_check_note": "",
    }
    return templates.get(k, k).format(**kw) if kw else templates.get(k, k)

cfg_file = tempfile.mktemp(suffix=".json")
with open(cfg_file, "w") as f:
    json.dump({"hotkeys": {
        "start_recording": "ctrl+shift+r",
        "stop_recording": "ctrl+shift+s",
    }}, f)

root = ctk.CTk()
root.title("CHK-113 Test")
root.geometry("620x320")
root.resizable(False, False)
root.attributes("-topmost", True)
root.lift()

cfg = ConfigStore(cfg_file)
panel = HotkeysPanel(master=root, config=cfg, t=t)
panel.pack(fill="both", expand=True)
panel.on_show()

def run_check():
    # Set the field to ctrl+c and trigger the conflict check
    panel._key_vars["start_recording"].set("ctrl+c")
    panel._check_conflict("start_recording", "ctrl+c")
    root.update()

    # Read warning label state
    warn = panel._warn_labels["start_recording"]
    color = warn.cget("text_color")
    text  = warn.cget("text")
    print(f"COLOR={color!r}", flush=True)
    print(f"TEXT={text!r}", flush=True)
    assert color == "#ff9800", f"Expected #ff9800, got {color!r}"

    # Proceed anyway: save
    panel._save()
    saved = cfg.get("hotkeys", {})
    print(f"SAVED_BINDINGS={saved!r}", flush=True)
    assert saved.get("start_recording") == "ctrl+c", f"Expected ctrl+c saved, got {saved!r}"
    print("SAVE_OK", flush=True)

    # Screenshot
    root.after(300, take_shot)

def take_shot():
    from PIL import ImageGrab
    out = r"H:\Users\Leo1\SpeechRecognition\screens\chk_113_panel.png"
    x, y = root.winfo_rootx(), root.winfo_rooty()
    w, h = root.winfo_width(), root.winfo_height()
    try:
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(out)
        print(f"SCREENSHOT={out}", flush=True)
    except Exception as e:
        print(f"SCREENSHOT_FAIL={e}", flush=True)
    root.after(200, root.destroy)

root.after(400, run_check)
root.mainloop()

try: os.unlink(cfg_file)
except: pass

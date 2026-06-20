"""CHK-112: clipboard-only + file input → informational warning visible."""
import sys, os, json, tempfile
sys.path.insert(0, r"H:\Users\Leo1\SpeechRecognition\src")

import customtkinter as ctk
from gui.panels.output_config import OutputConfigPanel
from config.store import ConfigStore
from PIL import ImageGrab

def t(k, **kw):
    strings = {
        "output_fields_section": "Output Fields",
        "output_field_timestamp": "Timestamp",
        "output_field_speaker": "Speaker",
        "output_field_language": "Language",
        "output_field_confidence": "Confidence",
        "output_field_text": "Text",
        "output_field_translation": "Translation",
        "output_formats_section": "Formats",
        "output_dest_section": "Destinations",
        "output_dest_file": "Save to file",
        "output_dest_display": "Show in window",
        "output_dest_clipboard": "Copy to clipboard",
        "output_clipboard_file_warning": "Clipboard output is unavailable for file input sources.",
        "output_combine_section": "Combine segments",
        "output_combine_label": "Combine consecutive segments",
        "output_folder_label": "Output folder",
        "btn_browse": "Browse",
    }
    return strings.get(k, k).format(**kw) if kw else strings.get(k, k)

cfg_file = tempfile.mktemp(suffix=".json")
with open(cfg_file, "w") as f:
    json.dump({
        "output_to_clipboard": False,
        "output_to_file": True,
        "output_to_display": True,
        "output_formats": ["txt"],
    }, f)

root = ctk.CTk()
root.title("CHK-112 Test")
root.geometry("520x600")
root.attributes("-topmost", True)
root.lift()

cfg = ConfigStore(cfg_file)
panel = OutputConfigPanel(master=root, config=cfg, t=t)
panel.pack(fill="both", expand=True)
panel.on_show()

result = {}

def run_test():
    # Step 1: Uncheck all file formats
    for var in panel._format_vars.values():
        var.set(False)
    panel._save_formats()

    # Step 2: Enable clipboard-only
    panel._dest_clipboard.set(True)
    panel._on_clipboard_dest()

    root.update()

    # Check warning is visible
    warn_vis = panel._clipboard_warn.winfo_viewable()
    warn_text = panel._clipboard_warn.cget("text")
    result["warn_visible"] = warn_vis
    result["warn_text"] = warn_text
    print(f"WARN_VISIBLE={warn_vis}", flush=True)
    print(f"WARN_TEXT={warn_text!r}", flush=True)
    assert warn_vis, "Warning should be visible when clipboard-only"
    print("STEP1_PASS: warning shown", flush=True)

    # Step 3: Re-enable TXT → warning should disappear
    panel._format_vars["txt"].set(True)
    panel._save_formats()
    root.update()
    warn_vis2 = panel._clipboard_warn.winfo_viewable()
    result["warn_visible_after"] = warn_vis2
    print(f"WARN_VISIBLE_AFTER={warn_vis2}", flush=True)
    assert not warn_vis2, "Warning should hide when a format is also active"
    print("STEP2_PASS: warning hidden", flush=True)

    # Screenshot with warning shown
    panel._format_vars["txt"].set(False)
    panel._save_formats()
    root.update()
    root.after(300, take_shot)

def take_shot():
    x, y = root.winfo_rootx(), root.winfo_rooty()
    w, h = root.winfo_width(), root.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    out = r"H:\Users\Leo1\SpeechRecognition\screens\chk_112_panel.png"
    img.save(out)
    print(f"SCREENSHOT={out}", flush=True)
    root.after(200, root.destroy)

root.after(400, run_test)
root.mainloop()

try: os.unlink(cfg_file)
except: pass

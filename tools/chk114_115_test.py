"""CHK-114 and CHK-115 automated verification.

CHK-114: Speaker labelling prompt -- confirm Speaker 1 (name saved),
         cancel/skip Speaker 2 (retains 'Speaker 2' label).
CHK-115: Ctrl+Z in the labelling prompt reverts the typed label.
"""
import sys, os, json, tempfile, wave, struct, shutil
sys.path.insert(0, r"H:\Users\Leo1\SpeechRecognition\src")

import customtkinter as ctk
from gui.panels.profile_dialog import ProfileDialog
from config.store import ConfigStore
from library.storage import LibraryStorage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STRINGS = {
    "dialog_edit_profile": "Edit Profile",
    "profile_samples_section": "Samples",
    "btn_add_sample": "Add Sample",
    "profile_no_samples": "No samples",
    "btn_play": "Play", "btn_stop": "Stop",
    "btn_remove_sample": "Remove",
    "delete_confirm_title": "Delete?",
    "profile_lastname": "Last name",
    "profile_firstname": "First name",
    "profile_middlename": "Middle name",
    "profile_nickname": "Nickname",
    "profile_organisation": "Organisation",
    "profile_position": "Position",
    "profile_note": "Note",
    "btn_cancel": "Skip",
    "btn_confirm": "Confirm",
    "error_title": "Error",
    "profile_retraining": "Retraining...",
    "profile_retrain_single_done": "Done",
}

def t(k, **kw):
    s = STRINGS.get(k, k)
    return s.format(**kw) if kw else s


def make_library_with_sample(base: str) -> tuple[str, str]:
    """Create a temp library root, one profile with one WAV sample.
    Returns (library_root, folder_name)."""
    library_root = os.path.join(base, "library")
    storage = LibraryStorage(library_root)
    folder_name, _ = storage.create_profile()

    # Minimal silent WAV: 0.5 s, 16 kHz, mono, 16-bit
    sample_path = storage.sample_path(folder_name, "sample_001.wav")
    n_frames = 8000
    with wave.open(str(sample_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * n_frames)

    meta = storage.read_meta(folder_name)
    meta.samples.append("sample_001.wav")
    meta.sample_count = 1
    storage.write_meta(folder_name, meta)
    return library_root, folder_name


# ---------------------------------------------------------------------------
# CHK-114
# ---------------------------------------------------------------------------

def test_chk114():
    print("\n=== CHK-114 ===", flush=True)
    tmpdir = tempfile.mkdtemp(prefix="chk114_")
    try:
        library_root, folder_name = make_library_with_sample(tmpdir)
        cfg_path = os.path.join(tmpdir, "config.json")
        with open(cfg_path, "w") as f:
            json.dump({"library_root": library_root}, f)
        cfg = ConfigStore(cfg_path)

        root = ctk.CTk()
        root.withdraw()
        root.attributes("-topmost", True)

        results = {}

        # --- Dialog 1: Confirm (label Speaker 1) ---
        def on_done_1(fn):
            results["confirm_fn"] = fn
            root.after(0, open_dialog_2)

        dlg1 = ProfileDialog(root, cfg, t,
                             folder_name=folder_name, on_done=on_done_1)
        dlg1.attributes("-topmost", True)

        def fill_and_confirm():
            dlg1._name_vars["lastname"].set("Smith")
            dlg1._name_vars["firstname"].set("John")
            root.after(0, dlg1._confirm)

        dlg1.after(200, fill_and_confirm)

        # --- Dialog 2: Cancel (skip Speaker 2) ---
        folder2 = None

        def open_dialog_2():
            nonlocal folder2
            storage = LibraryStorage(library_root)
            fn2, _ = storage.create_profile()
            folder2 = fn2

            # Add a sample to fn2 so Confirm is enabled (even though we Cancel)
            sp = storage.sample_path(fn2, "sample_001.wav")
            with wave.open(str(sp), "w") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
                wf.writeframes(b"\x00\x00" * 8000)
            meta2 = storage.read_meta(fn2)
            meta2.samples.append("sample_001.wav"); meta2.sample_count = 1
            storage.write_meta(fn2, meta2)

            def on_done_2(fn):
                results["cancel_fn"] = fn
                root.after(100, root.destroy)

            dlg2 = ProfileDialog(root, cfg, t,
                                 folder_name=fn2, on_done=on_done_2)
            dlg2.attributes("-topmost", True)
            dlg2.after(200, dlg2._cancel)  # Skip

        root.mainloop()

        # --- Assertions ---
        fn1 = results.get("confirm_fn")
        assert fn1 is not None, f"Confirm on_done should pass folder_name, got {fn1!r}"
        storage = LibraryStorage(library_root)
        meta = storage.read_meta(fn1)
        assert meta.last_name == "Smith", f"last_name not saved: {meta.last_name!r}"
        assert meta.first_name == "John", f"first_name not saved: {meta.first_name!r}"
        print(f"  Speaker 1 confirmed as '{meta.last_name} {meta.first_name}'", flush=True)

        fn2 = results.get("cancel_fn")
        assert fn2 is None, f"Cancel on_done should pass None, got {fn2!r}"
        print("  Speaker 2 skipped (Cancel -> None)", flush=True)

        print("CHK-114: PASS", flush=True)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# CHK-115
# ---------------------------------------------------------------------------

def test_chk115():
    print("\n=== CHK-115 ===", flush=True)
    tmpdir = tempfile.mkdtemp(prefix="chk115_")
    try:
        library_root, folder_name = make_library_with_sample(tmpdir)
        cfg_path = os.path.join(tmpdir, "config.json")
        with open(cfg_path, "w") as f:
            json.dump({"library_root": library_root}, f)
        cfg = ConfigStore(cfg_path)

        root = ctk.CTk()
        root.withdraw()
        root.attributes("-topmost", True)

        results = {}

        def on_done(fn):
            results["fn"] = fn
            root.after(100, root.destroy)

        dlg = ProfileDialog(root, cfg, t,
                            folder_name=folder_name, on_done=on_done)
        dlg.attributes("-topmost", True)

        def run_undo_test():
            # Type an incorrect label into the last_name field
            var = dlg._name_vars["lastname"]
            var.set("WrongName")
            print(f"  After set('WrongName'): {var.get()!r}", flush=True)

            # Call _revert_field directly — same code path as Ctrl+Z binding
            dlg._revert_field(var, "lastname")
            reverted = var.get()
            print(f"  After _revert_field (Ctrl+Z handler): {reverted!r}", flush=True)
            results["reverted"] = reverted

            # Now cancel (don't save)
            root.after(0, dlg._cancel)

        dlg.after(300, run_undo_test)
        root.mainloop()

        reverted = results.get("reverted", "NOT_SET")
        # For a new profile, initial value is ""
        assert reverted == "", (
            f"Expected field to revert to '' (new profile), got {reverted!r}")
        print("  last_name reverted to empty string after Ctrl+Z", flush=True)
        print("CHK-115: PASS", flush=True)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Also test that Ctrl+Z binding fires on the actual entry widget
# ---------------------------------------------------------------------------

def test_chk115_binding():
    """Verify that the Ctrl+Z binding is registered on all name entry inner widgets."""
    print("\n=== CHK-115 binding (code inspection) ===", flush=True)
    tmpdir = tempfile.mkdtemp(prefix="chk115b_")
    try:
        library_root, folder_name = make_library_with_sample(tmpdir)
        cfg_path = os.path.join(tmpdir, "config.json")
        with open(cfg_path, "w") as f:
            json.dump({"library_root": library_root}, f)
        cfg = ConfigStore(cfg_path)

        root = ctk.CTk()
        root.withdraw()

        results = {}

        def on_done(fn):
            root.after(100, root.destroy)

        dlg = ProfileDialog(root, cfg, t,
                            folder_name=folder_name, on_done=on_done)

        def check_binding():
            bound_keys = []
            for field, entry_widget in dlg._name_entries.items():
                inner = entry_widget._entry
                # .bind("<Control-z>") with no callback returns the current binding script
                script = inner.bind("<Control-z>")
                if script:
                    bound_keys.append(field)
            results["bound_fields"] = bound_keys
            print(f"  Fields with <Control-z> binding: {bound_keys}", flush=True)
            root.after(0, dlg._cancel)

        dlg.after(200, check_binding)
        root.mainloop()

        expected_fields = ["lastname", "firstname", "middlename",
                           "nickname", "organisation", "position", "note"]
        for f in expected_fields:
            assert f in results.get("bound_fields", []), \
                f"Field '{f}' is missing Ctrl+Z binding"
        print("CHK-115 binding: PASS -- all 7 fields have <Control-z> bound", flush=True)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_chk114()
    test_chk115()
    test_chk115_binding()
    print("\nAll CHK-114/115 checks PASS", flush=True)

"""Right-click context menu and keyboard shortcuts for CTkTextbox/CTkEntry."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

# Physical key codes on Windows (layout-independent, same as VK_* codes).
_KC_A = 65
_KC_C = 67
_KC_V = 86
_KC_X = 88


def bind_context_menu(
    widget,
    readonly: bool = False,
    t: Callable[[str], str] | None = None,
) -> None:
    """Attach a right-click context menu and keyboard shortcuts to a widget.

    Works with CTkTextbox (inner _textbox) and CTkEntry (inner _entry).
    Shortcuts use physical key codes so they work regardless of the active
    keyboard layout (Latin, Cyrillic, etc.):
      - Ctrl+A: Select All
      - Ctrl+C: Copy
      - Ctrl+V: Paste  (skipped when readonly)
      - Ctrl+X: Cut    (skipped when readonly)
    """
    inner = getattr(widget, "_textbox", None) or getattr(widget, "_entry", None)
    if inner is None:
        return

    is_text = hasattr(inner, "tag_add")  # tk.Text vs tk.Entry

    def _label(key: str, fallback: str) -> str:
        if t is not None:
            try:
                return t(key)
            except Exception:
                pass
        return fallback

    def _select_all(event=None):
        if is_text:
            inner.tag_add("sel", "1.0", "end")
            inner.mark_set("insert", "end")
        else:
            inner.select_range(0, "end")
            inner.icursor("end")
        return "break"

    def _copy(event=None):
        inner.event_generate("<<Copy>>")
        return "break"

    def _paste(event=None):
        inner.event_generate("<<Paste>>")
        return "break"

    def _cut(event=None):
        inner.event_generate("<<Cut>>")
        return "break"

    def _on_ctrl_key(event: tk.Event):
        kc = event.keycode
        if kc == _KC_A:
            return _select_all()
        if kc == _KC_C:
            return _copy()
        if not readonly:
            if kc == _KC_V:
                return _paste()
            if kc == _KC_X:
                return _cut()

    def show_menu(event: tk.Event) -> None:
        menu = tk.Menu(inner, tearoff=0)
        menu.add_command(
            label=_label("ctx_select_all", "Select All"),
            command=_select_all,
        )
        menu.add_command(
            label=_label("ctx_copy", "Copy"),
            command=_copy,
        )
        if not readonly:
            menu.add_command(
                label=_label("ctx_paste", "Paste"),
                command=_paste,
            )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    inner.bind("<Button-3>", show_menu, add=True)
    inner.bind("<Control-Key>", _on_ctrl_key, add=True)

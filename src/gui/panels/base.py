"""Base panel class shared by all nine side panels."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class BasePanel(ctk.CTkFrame):
    """Abstract base for all side panels.

    Subclasses must implement :meth:`build` and may override
    :meth:`update_strings` to refresh labels after a language change.

    Parameters
    ----------
    master:
        Parent widget (the main content area).
    config:
        Application ``ConfigStore`` instance.
    t:
        Translation callable ``t(key, **kwargs) → str``.
    """

    def __init__(self, master, config, t: Callable[[str], str],
                 **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._config = config
        self._t = t
        self.build()

    # ------------------------------------------------------------------
    # Subclass interface
    # ------------------------------------------------------------------

    def build(self) -> None:
        """Build all child widgets.  Called once from __init__."""
        raise NotImplementedError

    def update_strings(self, t: Callable[[str], str]) -> None:
        """Re-apply translated strings.  Override to update widget text."""
        self._t = t

    def on_show(self) -> None:
        """Called when this panel becomes visible.  Override if needed."""

    def on_hide(self) -> None:
        """Called when this panel is hidden.  Override if needed."""

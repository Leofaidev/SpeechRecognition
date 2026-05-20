"""UI language loader (T-77).

Loads a JSON language file from the languages/ directory.  Falls back to the
English built-in strings if a key is missing.  Restores a corrupted or missing
file from the protected backup in languages/backup/.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


_LANG_DIR_NAME = "languages"
_BACKUP_DIR_NAME = "backup"
_DEFAULT_CODE = "en"

# Resolved at load time — overrideable for tests
_lang_dir: Path | None = None


def _resolve_lang_dir() -> Path:
    global _lang_dir
    if _lang_dir is not None:
        return _lang_dir
    here = Path(__file__).resolve()
    # Walk up until we find the languages/ sibling of src/
    for parent in here.parents:
        candidate = parent / _LANG_DIR_NAME
        if candidate.is_dir():
            return candidate
    # Fallback: assume languages/ is next to the running script's cwd
    return Path(_LANG_DIR_NAME)


class LangLoadError(Exception):
    """Raised when a language file cannot be loaded or restored."""


class LangManager:
    """Manages UI language strings.

    Parameters
    ----------
    lang_code:
        BCP-47-style code matching a JSON file name, e.g. ``"en"``, ``"fi"``,
        ``"zh_CN"``.
    lang_dir:
        Directory containing ``<code>.json`` files.  Defaults to the
        ``languages/`` folder at the project root.
    """

    def __init__(self, lang_code: str = _DEFAULT_CODE,
                 lang_dir: Path | None = None) -> None:
        self._dir = Path(lang_dir) if lang_dir else _resolve_lang_dir()
        self._strings: dict[str, str] = {}
        self._en_fallback: dict[str, str] = {}
        self._code = lang_code
        self._load_english_fallback()
        if lang_code != _DEFAULT_CODE:
            self.load(lang_code)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, lang_code: str) -> None:
        """Load strings for *lang_code*.  Restores from backup on corruption."""
        self._code = lang_code
        path = self._dir / f"{lang_code}.json"
        try:
            data = self._read_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            data = self._restore_from_backup(lang_code, path, exc)
        except FileNotFoundError as exc:
            data = self._restore_from_backup(lang_code, path, exc)
        self._strings = {k: v for k, v in data.items()
                         if not k.startswith("_")}

    def t(self, key: str, **kwargs: Any) -> str:
        """Return the translated string for *key*, with optional format kwargs."""
        template = (self._strings.get(key)
                    or self._en_fallback.get(key)
                    or key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, IndexError):
                return template
        return template

    @property
    def code(self) -> str:
        return self._code

    @property
    def available(self) -> list[str]:
        """Return list of language codes that have a JSON file present."""
        return sorted(
            p.stem for p in self._dir.glob("*.json")
            if not p.stem.startswith("_")
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_english_fallback(self) -> None:
        path = self._dir / f"{_DEFAULT_CODE}.json"
        try:
            data = self._read_json(path)
            self._en_fallback = {k: v for k, v in data.items()
                                  if not k.startswith("_")}
            if self._code == _DEFAULT_CODE:
                self._strings = dict(self._en_fallback)
        except Exception:
            self._en_fallback = {}

    @staticmethod
    def _read_json(path: Path) -> dict:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _restore_from_backup(self, lang_code: str, path: Path,
                              original_exc: Exception) -> dict:
        backup_path = self._dir / _BACKUP_DIR_NAME / f"{lang_code}.json"
        if not backup_path.exists():
            raise LangLoadError(
                f"Language file '{path}' missing/corrupt and no backup found."
            ) from original_exc
        try:
            shutil.copy2(backup_path, path)
            return self._read_json(path)
        except Exception as exc:
            raise LangLoadError(
                f"Could not restore language file '{path}' from backup."
            ) from exc

"""Substitution dictionary persistence layer — load/save as JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class DictEntry:
    source: str      # original term (may include fnmatch wildcards)
    replacement: str
    flags: str = ""  # e.g. "wildcard", "case-sensitive"


class DictionaryStore:
    """In-memory dictionary with JSON persistence.

    Parameters
    ----------
    path:
        Path to the JSON file.  Pass ``None`` for an in-memory-only store
        (useful in tests).
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else None
        self._entries: dict[str, DictEntry] = {}  # keyed by source.lower()
        if self._path is not None:
            self._load()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, source: str, replacement: str, flags: str = "") -> bool:
        """Add an entry.  Returns False if the key already exists (conflict)."""
        key = source.lower()
        if key in self._entries:
            return False
        self._entries[key] = DictEntry(source=source, replacement=replacement, flags=flags)
        self._save()
        return True

    def update(self, source: str, replacement: str, flags: str = "") -> None:
        """Add or overwrite an entry."""
        key = source.lower()
        self._entries[key] = DictEntry(source=source, replacement=replacement, flags=flags)
        self._save()

    def remove(self, source: str) -> bool:
        """Remove an entry.  Returns False if not found."""
        key = source.lower()
        if key not in self._entries:
            return False
        del self._entries[key]
        self._save()
        return True

    def get(self, source: str) -> DictEntry | None:
        return self._entries.get(source.lower())

    def __iter__(self) -> Iterator[DictEntry]:
        return iter(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path and self._path.exists():
            try:
                with self._path.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                for item in data:
                    key = item["source"].lower()
                    self._entries[key] = DictEntry(**item)
            except (json.JSONDecodeError, KeyError, OSError):
                pass

    def _save(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {"source": e.source, "replacement": e.replacement, "flags": e.flags}
            for e in self._entries.values()
        ]
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

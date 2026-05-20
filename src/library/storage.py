"""Voice profile library storage layer (T-41, T-42).

Library root contains speaker subfolders. Each subfolder has:
  speaker.json, sample_001.mp3 ... sample_NNN.mp3, embedding.npy
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# Windows-invalid filename chars (also forbid backslash and NUL)
_INVALID_CHARS = re.compile(r'[/\\:*?"<>|\x00]')
_SAMPLE_PATTERN = re.compile(r"^sample_(\d{3})\.mp3$")


# ---------------------------------------------------------------------------
# speaker.json data model
# ---------------------------------------------------------------------------

@dataclass
class SpeakerMeta:
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    nickname: str = ""
    organisation: str = ""
    position: str = ""
    note: str = ""
    creation_date: str = ""
    model_checksum: str = ""
    sample_count: int = 0
    samples: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    low_confidence: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SpeakerMeta":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Folder name generation (T-42)
# ---------------------------------------------------------------------------

def _sanitise(value: str) -> str:
    """Replace invalid Windows filename chars with underscore."""
    return _INVALID_CHARS.sub("_", value)


def make_folder_name(
    last: str,
    first: str,
    middle: str,
    nickname: str,
    *,
    library_root: Path | None = None,
) -> tuple[str, str]:
    """Generate the folder name and possibly auto-assign a nickname.

    Returns
    -------
    (folder_name, resolved_nickname)
    """
    parts = [
        _sanitise(last),
        _sanitise(first),
        _sanitise(middle),
        _sanitise(nickname),
    ]
    folder = "_".join(parts)

    if folder == "___":
        # All four parts empty → auto-assign
        resolved_nickname = _next_auto_id(library_root)
        folder = f"____{resolved_nickname.lstrip('#')}"
        return folder, resolved_nickname

    # If nickname part is empty but others are set, folder ends with _
    # That is correct per the spec example: Smith_John__ for middle=empty, nickname=empty
    return folder, nickname


def _next_auto_id(library_root: Path | None) -> str:
    """Return the next unused #NNN auto-ID by scanning existing ____NNN folders."""
    used: set[int] = set()
    if library_root and library_root.exists():
        for d in library_root.iterdir():
            if d.is_dir() and d.name.startswith("____"):
                try:
                    used.add(int(d.name[4:]))
                except ValueError:
                    pass
    n = 1
    while n in used:
        n += 1
    return f"#{n:03d}"


# ---------------------------------------------------------------------------
# LibraryStorage
# ---------------------------------------------------------------------------

class LibraryStorage:
    """Manage the voice profile library on disk.

    Parameters
    ----------
    library_root:
        Directory that contains all speaker subfolders.
    """

    def __init__(self, library_root: Path | str) -> None:
        self._root = Path(library_root)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    # ------------------------------------------------------------------
    # profile discovery
    # ------------------------------------------------------------------

    def list_profiles(self) -> list[Path]:
        """Return all speaker subfolder paths (those containing speaker.json)."""
        return sorted(
            d for d in self._root.iterdir()
            if d.is_dir() and (d / "speaker.json").exists()
        )

    def profile_path(self, folder_name: str) -> Path:
        return self._root / folder_name

    # ------------------------------------------------------------------
    # speaker.json CRUD
    # ------------------------------------------------------------------

    def read_meta(self, folder_name: str) -> SpeakerMeta:
        path = self._root / folder_name / "speaker.json"
        with path.open(encoding="utf-8") as fh:
            return SpeakerMeta.from_dict(json.load(fh))

    def write_meta(self, folder_name: str, meta: SpeakerMeta) -> None:
        folder = self._root / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "speaker.json").open("w", encoding="utf-8") as fh:
            json.dump(meta.to_dict(), fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # profile lifecycle
    # ------------------------------------------------------------------

    def create_profile(
        self,
        last: str = "",
        first: str = "",
        middle: str = "",
        nickname: str = "",
        organisation: str = "",
        position: str = "",
        note: str = "",
        model_checksum: str = "",
    ) -> tuple[str, SpeakerMeta]:
        """Create a new speaker subfolder and initial speaker.json.

        Returns ``(folder_name, meta)``.
        """
        folder_name, resolved_nickname = make_folder_name(
            last, first, middle, nickname, library_root=self._root
        )
        folder = self._root / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        meta = SpeakerMeta(
            last_name=last,
            first_name=first,
            middle_name=middle,
            nickname=resolved_nickname,
            organisation=organisation,
            position=position,
            note=note,
            creation_date=datetime.now(timezone.utc).isoformat(),
            model_checksum=model_checksum,
            sample_count=0,
            samples=[],
            groups=[],
            low_confidence=False,
        )
        self.write_meta(folder_name, meta)
        return folder_name, meta

    def delete_profile(self, folder_name: str) -> None:
        """Remove a speaker subfolder and update all groups that referenced them."""
        folder = self._root / folder_name
        if not folder.exists():
            return

        # Remove speaker from all groups
        for profile_path in self.list_profiles():
            if profile_path.name == folder_name:
                continue
            meta = self.read_meta(profile_path.name)
            if folder_name in meta.groups:
                meta.groups = [g for g in meta.groups if g != folder_name]
                self.write_meta(profile_path.name, meta)

        shutil.rmtree(folder)

    def rename_profile(self, old_folder: str, new_folder: str) -> None:
        """Rename a speaker subfolder and update all group membership references."""
        old_path = self._root / old_folder
        new_path = self._root / new_folder
        if not old_path.exists():
            raise FileNotFoundError(f"Profile not found: {old_folder}")
        old_path.rename(new_path)

        # Update references in all other profiles' groups arrays
        for profile_path in self.list_profiles():
            if profile_path.name == new_folder:
                continue
            meta = self.read_meta(profile_path.name)
            if old_folder in meta.groups:
                meta.groups = [
                    new_folder if g == old_folder else g for g in meta.groups
                ]
                self.write_meta(profile_path.name, meta)

    # ------------------------------------------------------------------
    # sample file helpers
    # ------------------------------------------------------------------

    def next_sample_name(self, folder_name: str) -> str:
        """Return the next available sample filename, e.g. 'sample_003.mp3'."""
        folder = self._root / folder_name
        existing = {
            int(m.group(1))
            for f in folder.iterdir()
            if (m := _SAMPLE_PATTERN.match(f.name))
        } if folder.exists() else set()
        n = 1
        while n in existing:
            n += 1
        return f"sample_{n:03d}.mp3"

    def sample_path(self, folder_name: str, sample_name: str) -> Path:
        return self._root / folder_name / sample_name

    def embedding_path(self, folder_name: str) -> Path:
        return self._root / folder_name / "embedding.npy"

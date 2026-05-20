"""Import substitution dictionary entries from a CSV file.

CSV format (no header required, but tolerated):
    source,replacement[,flags]

ImportResult reports new entries added and conflicts rejected.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dictionary.store import DictionaryStore


@dataclass
class ImportResult:
    added: int = 0
    rejected: int = 0
    rejected_sources: list[str] = field(default_factory=list)


def import_csv(path: Path | str, store: "DictionaryStore") -> ImportResult:
    """Parse *path* and add new entries to *store*.

    Rows that conflict with existing entries are rejected (not overwritten).
    Returns an ImportResult summary.
    """
    path = Path(path)
    result = ImportResult()

    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row:
                continue
            # Skip header row if present
            if row[0].lower().strip() == "source":
                continue
            if len(row) < 2:
                continue

            source = row[0].strip()
            replacement = row[1].strip()
            flags = row[2].strip() if len(row) > 2 else ""

            if not source or not replacement:
                continue

            added = store.add(source, replacement, flags)
            if added:
                result.added += 1
            else:
                result.rejected += 1
                result.rejected_sources.append(source)

    return result

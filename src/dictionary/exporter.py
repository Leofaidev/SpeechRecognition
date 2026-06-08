"""Export substitution dictionary to a CSV file."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dictionary.store import DictionaryStore


def export_csv(store: "DictionaryStore", path: Path | str) -> int:
    """Write all entries in *store* to a CSV file.

    Returns the number of rows written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source", "replacement"])
        for entry in store:
            writer.writerow([entry.source, entry.replacement])
            count += 1

    return count

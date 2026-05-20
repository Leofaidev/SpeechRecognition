"""Output file naming following the _WSP convention.

Rules (Spec 8.3)
----------------
- Base name: <input_stem>_WSP.<ext>
- Collision avoidance: _WSP_2, _WSP_3, ... when file already exists.
- Stream splits: _WSP_part1.<ext>, _WSP_part2.<ext>, ...
"""

from __future__ import annotations

from pathlib import Path


def make_output_path(
    input_path: Path | str,
    extension: str,
    output_dir: Path | str | None = None,
    part: int | None = None,
) -> Path:
    """Generate a collision-safe output path for *input_path*.

    Parameters
    ----------
    input_path:
        Original input file (or a stem for microphone sessions).
    extension:
        Target extension including the dot, e.g. ".txt".
    output_dir:
        Directory for the output file.  Defaults to the same directory as
        *input_path* (or CWD if *input_path* is just a name).
    part:
        If provided, generates a ``_partN`` path for a split stream.
        Collision avoidance is still applied.

    Returns
    -------
    A Path that does not yet exist (unless all candidates are occupied, in
    which case the highest-numbered candidate is returned).
    """
    input_path = Path(input_path)
    stem = input_path.stem
    directory = Path(output_dir) if output_dir is not None else input_path.parent

    if part is not None:
        base_name = f"{stem}_WSP_part{part}{extension}"
    else:
        base_name = f"{stem}_WSP{extension}"

    candidate = directory / base_name
    if not candidate.exists():
        return candidate

    # Collision: try _WSP_2, _WSP_3, ... (or _WSP_part1_2, ...)
    suffix = 2
    while True:
        if part is not None:
            name = f"{stem}_WSP_part{part}_{suffix}{extension}"
        else:
            name = f"{stem}_WSP_{suffix}{extension}"
        candidate = directory / name
        if not candidate.exists():
            return candidate
        suffix += 1
        if suffix > 9999:
            return candidate  # safety valve

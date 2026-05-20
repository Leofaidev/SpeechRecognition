"""CHK-146 — CLI batch processing via subprocess.

Invokes the CLI entry point (cli.parser.main) directly:
  python -m cli.parser --input a.wav b.wav --output-format txt json

Expects:
- Exit code 0
- Two input files × two formats = four output files written
- All four files contain _WSP in their name

Requires faster-whisper tiny model.  Pass --integration to run.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"
SRC = Path(__file__).parent.parent.parent / "src"


@pytest.mark.integration
def test_cli_batch_txt_and_json(tmp_path):
    """Two input files + --output-format txt json → 4 output files, exit 0.
    (CHK-146)
    """
    result = subprocess.run(
        [
            sys.executable, "-m", "cli.parser",
            "--input",
            str(FIXTURES / "english_10s.wav"),
            str(FIXTURES / "short_1s.wav"),
            "--output-folder", str(tmp_path),
            "--output-format", "txt", "json",
        ],
        capture_output=True,
        text=True,
        cwd=str(SRC.parent),  # repo root so ConfigStore finds defaults
    )

    assert result.returncode == 0, (
        f"CLI exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    txt_files = list(tmp_path.glob("*_WSP.txt"))
    json_files = list(tmp_path.glob("*_WSP.json"))
    assert len(txt_files) == 2, f"Expected 2 TXT files, got {[f.name for f in txt_files]}"
    assert len(json_files) == 2, f"Expected 2 JSON files, got {[f.name for f in json_files]}"


@pytest.mark.integration
def test_cli_single_file_exit_zero(tmp_path):
    """Single input file produces one output file and exits 0."""
    result = subprocess.run(
        [
            sys.executable, "-m", "cli.parser",
            "--input", str(FIXTURES / "english_10s.wav"),
            "--output-folder", str(tmp_path),
            "--output-format", "txt",
        ],
        capture_output=True,
        text=True,
        cwd=str(SRC.parent),
    )

    assert result.returncode == 0, (
        f"Unexpected exit code {result.returncode}.\n"
        f"stderr: {result.stderr}"
    )
    assert len(list(tmp_path.glob("*_WSP.txt"))) == 1


@pytest.mark.integration
def test_cli_nonexistent_file_exits_nonzero():
    """Passing a file that does not exist exits with code 3 (EXIT_FILE_NOT_FOUND)."""
    result = subprocess.run(
        [
            sys.executable, "-m", "cli.parser",
            "--input", "/no/such/file.wav",
        ],
        capture_output=True,
        text=True,
        cwd=str(SRC.parent),
    )

    assert result.returncode == 3, (
        f"Expected exit code 3, got {result.returncode}.\n"
        f"stderr: {result.stderr}"
    )


@pytest.mark.integration
def test_cli_no_input_exits_nonzero():
    """Calling CLI with no --input and no default last_input_files exits 2."""
    result = subprocess.run(
        [sys.executable, "-m", "cli.parser"],
        capture_output=True,
        text=True,
        cwd=str(SRC.parent),
    )
    assert result.returncode == 2, (
        f"Expected exit code 2, got {result.returncode}.\n"
        f"stderr: {result.stderr}"
    )

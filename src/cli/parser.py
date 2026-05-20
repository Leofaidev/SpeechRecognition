"""CLI argument parser for the Speech Recognition Program (T-67 to T-75).

Entry point: ``main(argv=None)``
Exit codes: 0 success, 1 bad param, 2 missing input, 3 file not found,
            4 output not writable, 5 session not found, 10 translation error,
            20 library error.

All output is always in English (Spec 15.1.b).
GUI is never launched from this module (Spec 15.1.a).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------

EXIT_SUCCESS = 0
EXIT_BAD_PARAM = 1
EXIT_MISSING_INPUT = 2
EXIT_FILE_NOT_FOUND = 3
EXIT_OUTPUT_NOT_WRITABLE = 4
EXIT_SESSION_NOT_FOUND = 5
EXIT_TRANSLATION_ERROR = 10
EXIT_LIBRARY_ERROR = 20


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Return a fully-configured ArgumentParser."""
    parser = argparse.ArgumentParser(
        prog="wsp",
        description="Speech Recognition Program — headless CLI",
        add_help=True,
        exit_on_error=False,  # so we can control the exit code
    )

    # Global options
    parser.add_argument("--input", "-i", nargs="+", metavar="FILE",
                        help="One or more input files (MP3, WAV, MP4, AVI).")
    parser.add_argument("--output-folder", "-o", metavar="PATH",
                        help="Folder for output files.")
    parser.add_argument("--output-format", "-f", nargs="+",
                        choices=["txt", "docx", "srt", "json"],
                        metavar="FMT",
                        help="Output format(s): txt docx srt json.")
    parser.add_argument("--source-language", "-l", metavar="LANG",
                        help="Source language code (e.g. en, fi). Omit for auto-detect.")
    parser.add_argument("--target-language", "-t", metavar="LANG",
                        help="Translation target language code.")
    parser.add_argument("--speaker-group", "-g", metavar="NAME",
                        help="Voice library group for speaker identification.")
    parser.add_argument("--input-device", metavar="NAME",
                        help="Partial microphone/webcam device name.")
    parser.add_argument("--translation-engine", choices=["opus-mt", "google"],
                        metavar="ENGINE",
                        help="Translation engine: opus-mt (local) or google.")

    # Profile management
    parser.add_argument("--profile-create", action="store_true",
                        help="Create a voice profile from --audio.")
    parser.add_argument("--profile-delete", action="store_true",
                        help="Delete a voice profile by --name.")
    parser.add_argument("--profile-rename", action="store_true",
                        help="Rename a voice profile.")
    parser.add_argument("--audio", metavar="PATH",
                        help="Audio file for --profile-create.")
    parser.add_argument("--name", metavar="NAME",
                        help="Profile folder name for delete/rename.")
    parser.add_argument("--new-name", metavar="NAME",
                        help="New profile folder name for --profile-rename.")
    parser.add_argument("--lastname", metavar="NAME")
    parser.add_argument("--firstname", metavar="NAME")
    parser.add_argument("--middlename", metavar="NAME")
    parser.add_argument("--nickname", metavar="NAME")
    parser.add_argument("--organisation", metavar="NAME")
    parser.add_argument("--position", metavar="NAME")
    parser.add_argument("--note", metavar="TEXT")

    # Dictionary management
    parser.add_argument("--dict-export", metavar="PATH",
                        help="Export dictionary to a CSV file.")
    parser.add_argument("--dict-import", metavar="PATH",
                        help="Import entries from a CSV file.")

    # Backup / restore
    parser.add_argument("--backup", metavar="PATH",
                        help="Create a ZIP backup at PATH.")
    parser.add_argument("--restore", metavar="PATH",
                        help="Restore from a ZIP backup.")

    # Session history
    parser.add_argument("--list-sessions", action="store_true",
                        help="Print a table of all stored sessions.")
    parser.add_argument("--regenerate-output", action="store_true",
                        help="Regenerate output files for a session.")
    parser.add_argument("--session", metavar="SESSION_ID",
                        help="Session ID for --regenerate-output.")

    return parser


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_args(args: argparse.Namespace, config) -> tuple[bool, str, int]:
    """Validate parsed args against config defaults.

    Returns ``(ok, error_message, exit_code)``.
    """
    # Determine effective input files
    effective_input = args.input or config.get("last_input_files", [])

    # If no operation specified and no input: missing mandatory input
    operation = any([
        args.profile_create, args.profile_delete, args.profile_rename,
        args.dict_export, args.dict_import, args.backup, args.restore,
        args.list_sessions, args.regenerate_output,
    ])
    if not operation and not effective_input:
        return False, (
            "Missing mandatory input files. "
            "Provide at least one file with --input <file>, "
            "or use --help for usage."
        ), EXIT_MISSING_INPUT

    # Validate input files exist
    if args.input:
        for f in args.input:
            if not Path(f).exists():
                return False, f"Input file not found: {f}", EXIT_FILE_NOT_FOUND

    # Validate output folder is writable if specified
    if args.output_folder:
        out = Path(args.output_folder)
        try:
            out.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return False, f"Output folder not writable: {exc}", EXIT_OUTPUT_NOT_WRITABLE

    return True, "", EXIT_SUCCESS


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    """Parse *argv* and dispatch to the appropriate operation.

    Returns the exit code (0 = success).
    """
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except (argparse.ArgumentError, SystemExit) as exc:
        # argparse prints usage and exits; with exit_on_error=False it raises
        if isinstance(exc, SystemExit) and exc.code == 0:
            return EXIT_SUCCESS
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_BAD_PARAM

    # Lazy imports to avoid pulling in heavy deps for --help / unrecognised param
    from config.store import ConfigStore
    config = ConfigStore()

    ok, message, code = validate_args(args, config)
    if not ok:
        print(f"Error: {message}", file=sys.stderr)
        return code

    # HuggingFace licence warning (T-74)
    if not config.get("licence_accepted", False):
        print(
            "Warning: HuggingFace pyannote licence not accepted. "
            "Speaker identification is disabled. All speakers will be labelled Unknown.",
            file=sys.stdout,
        )

    return _dispatch(args, config)


def _dispatch(args: argparse.Namespace, config) -> int:
    if args.list_sessions:
        return _cmd_list_sessions(args, config)
    if args.regenerate_output:
        return _cmd_regenerate_output(args, config)
    if args.backup:
        return _cmd_backup(args, config)
    if args.restore:
        return _cmd_restore(args, config)
    if args.dict_import:
        return _cmd_dict_import(args, config)
    if args.dict_export:
        return _cmd_dict_export(args, config)
    if args.profile_create:
        return _cmd_profile_create(args, config)
    if args.profile_delete:
        return _cmd_profile_delete(args, config)
    if args.profile_rename:
        return _cmd_profile_rename(args, config)
    if args.input:
        return _cmd_process(args, config)
    return EXIT_SUCCESS


# ---------------------------------------------------------------------------
# Operation implementations
# ---------------------------------------------------------------------------

def _cmd_list_sessions(args, config) -> int:
    from session.history import print_session_list
    sessions_dir = Path(config.get("sessions_dir", "sessions"))
    print_session_list(sessions_dir)
    return EXIT_SUCCESS


def _cmd_regenerate_output(args, config) -> int:
    if not args.session:
        print("Error: --session SESSION_ID required with --regenerate-output.",
              file=sys.stderr)
        return EXIT_BAD_PARAM
    from session import history as sh
    sessions_dir = Path(config.get("sessions_dir", "sessions"))
    output_dir = Path(args.output_folder or config.get("output_folder") or ".")
    try:
        written = sh.regenerate_output(
            sessions_dir, args.session, output_dir,
            formats=args.output_format or config.get("output_formats", ["txt"]),
        )
    except FileNotFoundError:
        print(f"Error: Session '{args.session}' not found.", file=sys.stderr)
        return EXIT_SESSION_NOT_FOUND
    for p in written:
        print(f"Output written: {p}")
    return EXIT_SUCCESS


def _cmd_backup(args, config) -> int:
    from backup.manager import AppPaths, create_backup
    paths = _build_app_paths(config)
    result = create_backup(paths, Path(args.backup))
    if result.path_warning:
        print("Warning: Backup file is inside the installation folder.")
    print(f"Backup created: {result.zip_path} ({result.actual_size} bytes)")
    return EXIT_SUCCESS


def _cmd_restore(args, config) -> int:
    from backup.restorer import restore
    from backup.manager import AppPaths
    paths = _build_app_paths(config)
    safety_dir = Path(config.get("install_dir", ".")) / "backups"
    result = restore(paths, Path(args.restore), safety_dir)
    print(f"Safety backup created at: {result.safety_backup_path}")
    if not result.success:
        print(f"Error: Restore failed — {result.error}", file=sys.stderr)
        return EXIT_LIBRARY_ERROR
    print(f"Restore complete. ({result.restored_files} files restored)")
    return EXIT_SUCCESS


def _cmd_dict_import(args, config) -> int:
    from dictionary.store import DictionaryStore
    from dictionary.importer import import_csv
    dict_path = Path(config.get("dictionary_file", "dictionary.json"))
    store = DictionaryStore(dict_path)
    result = import_csv(Path(args.dict_import), store)
    print(f"Imported: {result.added} entries added, {result.rejected} rejected.")
    if result.rejected_sources:
        print(f"Rejected source words: {', '.join(repr(w) for w in result.rejected_sources)}")
    return EXIT_SUCCESS


def _cmd_dict_export(args, config) -> int:
    from dictionary.store import DictionaryStore
    from dictionary.exporter import export_csv
    dict_path = Path(config.get("dictionary_file", "dictionary.json"))
    store = DictionaryStore(dict_path)
    count = export_csv(store, Path(args.dict_export))
    print(f"Exported {count} entries to: {args.dict_export}")
    return EXIT_SUCCESS


def _cmd_profile_create(args, config) -> int:
    if not args.audio:
        print("Error: --audio PATH required with --profile-create.", file=sys.stderr)
        return EXIT_BAD_PARAM
    from audio.ingest import load
    from library.storage import LibraryStorage
    from library.profile_creator import ProfileCreator
    library_root = Path(config.get("library_root", "library"))
    try:
        audio, sr = load(args.audio)
    except FileNotFoundError:
        print(f"Error: Audio file not found: {args.audio}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    storage = LibraryStorage(library_root)
    creator = ProfileCreator(storage)
    folder, meta = creator.create(
        audio, sr,
        last=args.lastname or "",
        first=args.firstname or "",
        middle=args.middlename or "",
        nickname=args.nickname or "",
        organisation=args.organisation or "",
        position=args.position or "",
        note=args.note or "",
    )
    if meta.low_confidence:
        print("Warning: Audio shorter than 10 seconds — profile has low confidence.")
    print(f"Profile created: {folder}")
    return EXIT_SUCCESS


def _cmd_profile_delete(args, config) -> int:
    if not args.name:
        print("Error: --name required with --profile-delete.", file=sys.stderr)
        return EXIT_BAD_PARAM
    from library.storage import LibraryStorage
    library_root = Path(config.get("library_root", "library"))
    storage = LibraryStorage(library_root)
    storage.delete_profile(args.name)
    print(f"Profile deleted: {args.name}")
    return EXIT_SUCCESS


def _cmd_profile_rename(args, config) -> int:
    if not args.name or not args.new_name:
        print("Error: --name and --new-name required with --profile-rename.", file=sys.stderr)
        return EXIT_BAD_PARAM
    from library.storage import LibraryStorage
    library_root = Path(config.get("library_root", "library"))
    storage = LibraryStorage(library_root)
    try:
        storage.rename_profile(args.name, args.new_name)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_LIBRARY_ERROR
    print(f"Profile renamed: {args.name} -> {args.new_name}")
    return EXIT_SUCCESS


def _cmd_process(args, config) -> int:
    """Run the full pipeline for each input file."""
    from audio.ingest import load
    from diarization.engine import DiarizationEngine
    from transcription.engine import TranscriptionEngine
    from dictionary.store import DictionaryStore
    from dictionary.matcher import apply as dict_apply
    from translation.engine import TranslationEngine
    from output import txt_writer, srt_writer, json_writer, docx_writer
    from output.naming import make_output_path
    from session.manager import SessionManager
    from session import history as sh

    output_dir = Path(args.output_folder or config.get("output_folder") or ".")
    output_dir.mkdir(parents=True, exist_ok=True)
    formats = args.output_format or config.get("output_formats", ["txt"])

    dict_store = DictionaryStore(Path(config.get("dictionary_file", "dictionary.json")))
    diarizer = DiarizationEngine(config)
    transcriber = TranscriptionEngine(config)
    translator = TranslationEngine(config)

    for input_file in args.input:
        print(f"Processing: {input_file}")
        try:
            audio, sr = load(input_file)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_FILE_NOT_FOUND

        segments = diarizer.diarize_or_unknown(audio, sr)
        ts_segments = transcriber.transcribe(audio, segments, sr)
        ts_segments = dict_apply(dict_store, ts_segments)
        ts_segments = translator.translate(ts_segments)

        session = SessionManager(source_type="file", source_path=str(input_file),
                                 speaker_group=args.speaker_group or "")
        session.add_segments(ts_segments)

        written: list[Path] = []
        for fmt in formats:
            ext = f".{fmt}"
            out_path = make_output_path(Path(input_file), ext, output_dir)
            if fmt == "txt":
                txt_writer.write(ts_segments, out_path)
            elif fmt == "srt":
                srt_writer.write(ts_segments, out_path)
            elif fmt == "json":
                json_writer.write(ts_segments, out_path)
            elif fmt == "docx":
                docx_writer.write(ts_segments, out_path)
            written.append(out_path)
            print(f"  Output: {out_path}")

        session.output_files = [str(p) for p in written]
        sessions_dir = Path(config.get("sessions_dir", "sessions"))
        sh.save(sessions_dir, session)

    return EXIT_SUCCESS


def _build_app_paths(config):
    from backup.manager import AppPaths
    return AppPaths(
        config_file=Path(config.get("config_file", "config.json")),
        dictionary_file=Path(config.get("dictionary_file", "dictionary.json")),
        library_root=Path(config.get("library_root", "library")),
        sessions_dir=Path(config.get("sessions_dir", "sessions")),
        install_dir=Path(config.get("install_dir", ".")),
    )

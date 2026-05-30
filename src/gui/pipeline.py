"""Background pipeline runner (T-84, T-85).

Runs the full processing pipeline (diarization → transcription → dictionary →
translation → output) in a daemon thread so the GUI stays responsive.

Usage::

    runner = PipelineRunner(config, on_progress=..., on_done=..., on_error=...)
    runner.start_file("audio.mp3")          # Regular mode, file input
    runner.start_microphone(audio, sr)      # Regular mode, microphone
    runner.start_short_session(audio, sr)   # Short Session mode

All callbacks are called from the background thread.  The GUI must schedule
any UI updates via ``widget.after(0, callback)`` or a queue.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

from config.store import ConfigStore


@dataclass
class PipelineResult:
    """Holds the result of a completed pipeline run."""
    segments: list = field(default_factory=list)
    output_paths: list[Path] = field(default_factory=list)
    clipboard_text: str = ""
    source_path: str = ""
    error: str = ""
    # Set only when output is deferred for post-session speaker labelling.
    audio: object = field(default=None, repr=False)
    sample_rate: int = 16000
    write_output_fn: object = field(default=None, repr=False)

    @property
    def ok(self) -> bool:
        return not self.error


ProgressCallback = Callable[[float, str], None]
DoneCallback = Callable[[PipelineResult], None]
ErrorCallback = Callable[[str], None]


class PipelineRunner:
    """Manages a single pipeline thread.

    At most one pipeline run is active at a time.  Calling
    :meth:`start_file` or :meth:`start_microphone` while a run is active
    is a no-op.
    """

    def __init__(
        self,
        config: ConfigStore,
        on_progress: ProgressCallback | None = None,
        on_done: DoneCallback | None = None,
        on_error: ErrorCallback | None = None,
    ) -> None:
        self._config = config
        self._on_progress = on_progress or (lambda p, s: None)
        self._on_done = on_done or (lambda r: None)
        self._on_error = on_error or (lambda e: None)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        # Cached engine instances — models are loaded once and reused across runs.
        self._diarizer = None
        self._transcriber = None
        self._embedder = None   # pyannote embedding model for speaker matching

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start_file(self, path: str,
                   output_dir: Path | None = None,
                   formats: list[str] | None = None,
                   speaker_group: str = "") -> bool:
        """Start pipeline for a single file.  Returns False if already running."""
        if self.running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_file,
            args=(path, output_dir, formats, speaker_group),
            daemon=True,
        )
        self._thread.start()
        return True

    def start_microphone(self, audio, sample_rate: int,
                         output_dir: Path | None = None,
                         formats: list[str] | None = None,
                         speaker_group: str = "") -> bool:
        """Start pipeline for a microphone buffer."""
        if self.running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_microphone,
            args=(audio, sample_rate, output_dir, formats, speaker_group),
            daemon=True,
        )
        self._thread.start()
        return True

    def start_short_session(self, audio, sample_rate: int,
                             speaker_group: str = "") -> bool:
        """Start Short Session pipeline (auto-clipboard, no file output)."""
        if self.running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_short_session,
            args=(audio, sample_rate, speaker_group),
            daemon=True,
        )
        self._thread.start()
        return True

    def start_batch(self, paths: Sequence[str],
                    output_dir: Path | None = None,
                    formats: list[str] | None = None,
                    speaker_group: str = "",
                    on_file_done: Callable[[str, PipelineResult], None] | None = None,
                    on_batch_done: Callable[[list[str]], None] | None = None,
                    on_labelling_needed: Callable | None = None) -> bool:
        """Start batch processing of multiple files."""
        if self.running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_batch,
            args=(list(paths), output_dir, formats, speaker_group,
                  on_file_done, on_batch_done, on_labelling_needed),
            daemon=True,
        )
        self._thread.start()
        return True

    def request_stop(self) -> None:
        """Request the running pipeline to stop after the current segment."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Pipeline implementations (run in background thread)
    # ------------------------------------------------------------------

    def _run_file(self, path: str, output_dir, formats, speaker_group) -> None:
        try:
            result = self._execute_pipeline(
                source_type="file",
                source_path=path,
                audio=None,
                sample_rate=None,
                output_dir=output_dir,
                formats=formats,
                speaker_group=speaker_group,
                short_session=False,
            )
            self._on_done(result)
        except Exception as exc:
            self._on_error(str(exc))

    def _run_microphone(self, audio, sample_rate, output_dir, formats,
                        speaker_group) -> None:
        try:
            result = self._execute_pipeline(
                source_type="microphone",
                source_path="",
                audio=audio,
                sample_rate=sample_rate,
                output_dir=output_dir,
                formats=formats,
                speaker_group=speaker_group,
                short_session=False,
            )
            self._on_done(result)
        except Exception as exc:
            self._on_error(str(exc))

    def _run_short_session(self, audio, sample_rate, speaker_group) -> None:
        try:
            result = self._execute_pipeline(
                source_type="microphone",
                source_path="",
                audio=audio,
                sample_rate=sample_rate,
                output_dir=None,
                formats=None,
                speaker_group=speaker_group,
                short_session=True,
            )
            self._on_done(result)
        except Exception as exc:
            self._on_error(str(exc))

    def _run_batch(self, paths, output_dir, formats, speaker_group,
                   on_file_done, on_batch_done, on_labelling_needed=None) -> None:
        failed: list[str] = []
        n = len(paths)
        for i, path in enumerate(paths):
            if self._stop_event.is_set():
                break
            self._on_progress(i / n, path)
            try:
                result = self._execute_pipeline(
                    source_type="file",
                    source_path=path,
                    audio=None,
                    sample_rate=None,
                    output_dir=output_dir,
                    formats=formats,
                    speaker_group=speaker_group,
                    short_session=False,
                    force_file_output=True,
                )
                needs_labelling = (
                    result.ok and
                    result.write_output_fn is not None and
                    on_labelling_needed is not None and
                    self._config.get("output_fields", {}).get("speaker", True)
                )
                if needs_labelling:
                    # Block this thread while the user labels speakers in the UI.
                    done_event = threading.Event()
                    on_labelling_needed(result, done_event)
                    done_event.wait()
                    # write_output_fn was called by the labelling flow in app.py
                elif result.ok and result.write_output_fn:
                    result.write_output_fn()
                if on_file_done:
                    on_file_done(path, result)
                if not result.ok:
                    failed.append(path)
            except Exception as exc:
                failed.append(path)
                if on_file_done:
                    r = PipelineResult(source_path=path, error=str(exc))
                    on_file_done(path, r)
        self._on_progress(1.0, "")
        if on_batch_done:
            on_batch_done(failed)

    # ------------------------------------------------------------------
    # Core pipeline logic
    # ------------------------------------------------------------------

    def _execute_pipeline(
        self,
        source_type: str,
        source_path: str,
        audio,
        sample_rate,
        output_dir: Path | None,
        formats: list[str] | None,
        speaker_group: str,
        short_session: bool,
        force_file_output: bool = False,
    ) -> PipelineResult:
        from pathlib import Path as _Path
        from audio.ingest import load
        from diarization.engine import DiarizationEngine
        from transcription.engine import TranscriptionEngine
        from dictionary.store import DictionaryStore
        from dictionary.matcher import apply as dict_apply
        from translation.engine import TranslationEngine
        from output import txt_writer, srt_writer, json_writer, docx_writer
        from output.clipboard_writer import write as clipboard_write
        from output.naming import make_output_path
        from session.manager import SessionManager
        from session import history as sh

        config = self._config

        # Load audio if needed
        if audio is None:
            self._on_progress(0.05, "Loading audio...")
            audio, sample_rate = load(source_path)

        # Skip diarization when speaker output is disabled (Regular mode) or in
        # Short Session mode — Whisper segments the audio on its own.
        output_fields = config.get("output_fields", {})
        skip_diarization = short_session or not output_fields.get("speaker", True)

        if skip_diarization:
            if self._transcriber is None:
                self._transcriber = TranscriptionEngine(config)
            transcriber_loaded = self._transcriber._model is not None
            self._on_progress(
                0.30,
                "Transcribing..." if transcriber_loaded
                else "Loading speech model (first run, please wait)...",
            )
            ts_segments = self._transcriber.transcribe_without_diarization(
                audio, sample_rate)
        else:
            # Diarize — reuse cached engine so model stays in memory between runs
            if self._diarizer is None:
                self._diarizer = DiarizationEngine(config)
            diarizer_loaded = self._diarizer._pipeline is not None
            self._on_progress(
                0.15,
                "Diarizing..." if diarizer_loaded
                else "Loading speaker model (first run, please wait)...",
            )
            segments = self._diarizer.diarize_or_unknown(audio, sample_rate)

            if self._stop_event.is_set():
                return PipelineResult(error="Stopped by user.")

            # Match diarized speakers against voice profiles in the selected group
            if speaker_group:
                self._on_progress(0.28, "Matching speakers to group...")
                segments = self._match_speakers_to_group(
                    audio, sample_rate, segments, speaker_group)

            if self._stop_event.is_set():
                return PipelineResult(error="Stopped by user.")

            # Transcribe — reuse cached engine so Whisper stays in memory
            if self._transcriber is None:
                self._transcriber = TranscriptionEngine(config)
            transcriber_loaded = self._transcriber._model is not None
            self._on_progress(
                0.40,
                "Transcribing..." if transcriber_loaded
                else "Loading speech model (first run, please wait)...",
            )
            ts_segments = self._transcriber.transcribe(audio, segments, sample_rate)

        if self._stop_event.is_set():
            return PipelineResult(error="Stopped by user.")

        # Dictionary
        self._on_progress(0.65, "Applying dictionary...")
        dict_path = _Path(config.get("dictionary_file", "dictionary.json"))
        dict_store = DictionaryStore(dict_path)
        ts_segments = dict_apply(dict_store, ts_segments)

        # Translate
        self._on_progress(0.75, "Translating...")
        translator = TranslationEngine(config)
        ts_segments = translator.translate(ts_segments)

        # Build clipboard text
        clipboard_text = " ".join(
            seg.text for seg in ts_segments if seg.text and not seg.bad_audio
        )
        translated_text = " ".join(
            seg.translated_text or seg.text
            for seg in ts_segments if not seg.bad_audio
        )

        # Session
        session = SessionManager(
            source_type=source_type,
            source_path=source_path,
            speaker_group=speaker_group,
        )
        session.add_segments(ts_segments)

        # Detect unidentified speakers (Speaker N labels from diarization).
        # In non-short-session mode, defer output writing until after labelling.
        import re as _re
        unidentified = {
            seg.speaker_id for seg in ts_segments
            if _re.match(r'^Speaker \d+$', seg.speaker_id)
        }

        if unidentified and not short_session:
            # Capture everything the deferred writer needs.  ts_segments is
            # passed by reference so relabelling mutations are visible here.
            _segs = ts_segments
            _cfg = config
            _output_dir = output_dir
            _formats = formats
            _source_path = source_path
            _source_type = source_type
            _session = session

            _force = force_file_output

            def _write_output_deferred() -> list:
                written_d: list[_Path] = []
                if _force or _cfg.get("output_to_file", True):
                    eff_dir = _Path(_output_dir or _cfg.get("output_folder") or ".")
                    eff_dir.mkdir(parents=True, exist_ok=True)
                    eff_fmts = _formats or _cfg.get("output_formats", ["txt"])
                    inp = _Path(_source_path) if _source_path else _Path("output")
                    out_segs = _segs
                    _output_fields = _cfg.get("output_fields", None)
                    for fmt in eff_fmts:
                        out_path = make_output_path(inp, f".{fmt}", eff_dir)
                        if fmt == "txt":
                            txt_writer.write(out_segs, out_path, fields=_output_fields)
                        elif fmt == "srt":
                            srt_writer.write(out_segs, out_path, fields=_output_fields)
                        elif fmt == "json":
                            json_writer.write(out_segs, out_path)
                        elif fmt == "docx":
                            docx_writer.write(out_segs, out_path, fields=_output_fields)
                        written_d.append(out_path)
                if _cfg.get("output_to_clipboard", False):
                    try:
                        from output.clipboard_writer import _copy_to_clipboard
                        _use_trans = _cfg.get("translation_enabled", False)
                        _clip = " ".join(
                            (s.translated_text or s.text) if _use_trans else s.text
                            for s in _segs if not s.bad_audio
                        )
                        _copy_to_clipboard(_clip)
                    except Exception:
                        pass
                _session.output_files = [str(p) for p in written_d]
                sessions_dir_d = _Path(_cfg.get("sessions_dir", "sessions"))
                try:
                    sh.save(sessions_dir_d, _session)
                except Exception:
                    pass
                return written_d

            self._on_progress(1.0, "Done.")
            return PipelineResult(
                segments=ts_segments,
                output_paths=[],
                clipboard_text=translated_text if config.get("translation_enabled") else clipboard_text,
                source_path=source_path,
                audio=audio,
                sample_rate=sample_rate,
                write_output_fn=_write_output_deferred,
            )

        # No unidentified speakers (or short session) — write output immediately.
        self._on_progress(0.85, "Writing output...")
        written: list[Path] = []

        if not short_session:
            if force_file_output or config.get("output_to_file", True):
                eff_output_dir = _Path(
                    output_dir or config.get("output_folder") or "."
                )
                eff_output_dir.mkdir(parents=True, exist_ok=True)
                eff_formats = formats or config.get("output_formats", ["txt"])
                input_path = _Path(source_path) if source_path else _Path("output")
                out_segs = ts_segments
                output_fields = config.get("output_fields", None)

                for fmt in eff_formats:
                    out_path = make_output_path(input_path, f".{fmt}", eff_output_dir)
                    if fmt == "txt":
                        txt_writer.write(out_segs, out_path, fields=output_fields)
                    elif fmt == "srt":
                        srt_writer.write(out_segs, out_path, fields=output_fields)
                    elif fmt == "json":
                        json_writer.write(out_segs, out_path)
                    elif fmt == "docx":
                        docx_writer.write(out_segs, out_path, fields=output_fields)
                    written.append(out_path)

            if config.get("output_to_clipboard", False):
                try:
                    from output.clipboard_writer import _copy_to_clipboard
                    _clip = translated_text if config.get("translation_enabled") else clipboard_text
                    _copy_to_clipboard(_clip)
                except Exception:
                    pass

        session.output_files = [str(p) for p in written]
        sessions_dir = _Path(config.get("sessions_dir", "sessions"))
        try:
            sh.save(sessions_dir, session)
        except Exception:
            pass

        self._on_progress(1.0, "Done.")

        return PipelineResult(
            segments=ts_segments,
            output_paths=written,
            clipboard_text=translated_text if config.get("translation_enabled") else clipboard_text,
            source_path=source_path,
        )

    # ------------------------------------------------------------------
    # Speaker matching against a voice-profile group
    # ------------------------------------------------------------------

    def _match_speakers_to_group(
        self,
        audio,
        sample_rate: int,
        segments: list,
        speaker_group: str,
    ) -> list:
        """Relabel 'Speaker N' labels with profile names via embedding comparison.

        For each unique unidentified speaker, concatenates all their audio,
        computes a pyannote embedding, and compares it against every saved
        embedding in *speaker_group*.  Speakers whose cosine similarity
        exceeds MATCH_THRESHOLD are renamed to the matching profile name.
        Speakers with no match keep their 'Speaker N' label and will later
        trigger the manual labelling prompt.
        """
        import re
        from pathlib import Path as _Path
        import numpy as np

        library_root = _Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.groups import LibraryGroups
            storage = LibraryStorage(library_root)
            member_folders = LibraryGroups(storage).members(speaker_group)
        except Exception:
            return segments

        if not member_folders:
            return segments

        # Load saved embeddings for each group member
        profile_embeddings: dict[str, "np.ndarray"] = {}
        profile_display: dict[str, str] = {}
        for folder in member_folders:
            emb_path = storage.embedding_path(folder)
            if not emb_path.exists():
                continue
            try:
                emb = np.load(str(emb_path))
                meta = storage.read_meta(folder)
                parts = [meta.last_name, meta.first_name]
                full = " ".join(p for p in parts if p).strip()
                profile_display[folder] = full or meta.nickname or folder
                profile_embeddings[folder] = emb
            except Exception:
                continue

        if not profile_embeddings:
            return segments

        unidentified = {
            s.speaker_id for s in segments
            if re.match(r"^Speaker \d+$", s.speaker_id)
        }
        if not unidentified:
            return segments

        # Lazily load the embedding model using the same sub-model that the
        # diarization pipeline uses (already downloaded and licensed).
        try:
            import torch
            if self._embedder is None:
                from pyannote.audio.core.model import Model
                from pyannote.audio import Inference
                token = self._config.get("huggingface_token", None)
                hf_kwargs: dict = {"token": token} if token else {}
                # Derive model name from the loaded pipeline when available;
                # fall back to the known default for speaker-diarization-3.1.
                if (self._diarizer is not None and
                        self._diarizer._pipeline is not None and
                        isinstance(getattr(self._diarizer._pipeline,
                                           "embedding", None), str)):
                    emb_name = self._diarizer._pipeline.embedding
                else:
                    emb_name = "pyannote/wespeaker-voxceleb-resnet34-LM"
                emb_model = Model.from_pretrained(emb_name, **hf_kwargs)
                self._embedder = Inference(emb_model, window="whole")
        except Exception:
            return segments

        MATCH_THRESHOLD = 0.75

        speaker_match: dict[str, str] = {}
        for spk in unidentified:
            # Collect all audio segments for this speaker
            chunks = []
            for seg in segments:
                if seg.speaker_id != spk:
                    continue
                s_i = max(0, int(seg.start * sample_rate))
                e_i = min(len(audio), int(seg.end * sample_rate))
                if e_i > s_i:
                    chunks.append(audio[s_i:e_i])
            if not chunks:
                continue
            combined = np.concatenate(chunks)
            try:
                waveform = torch.tensor(combined).unsqueeze(0)
                q_emb = np.array(
                    self._embedder({"waveform": waveform, "sample_rate": sample_rate}))
            except Exception:
                continue

            best_score, best_folder = 0.0, None
            for folder, ref_emb in profile_embeddings.items():
                num = float(np.dot(q_emb.flatten(), ref_emb.flatten()))
                denom = float(np.linalg.norm(q_emb) * np.linalg.norm(ref_emb))
                sim = num / denom if denom > 0 else 0.0
                if sim > best_score:
                    best_score, best_folder = sim, folder

            if best_score >= MATCH_THRESHOLD and best_folder:
                speaker_match[spk] = profile_display[best_folder]

        if not speaker_match:
            return segments

        from dataclasses import replace as _replace
        return [
            _replace(seg, speaker_id=speaker_match.get(seg.speaker_id, seg.speaker_id))
            for seg in segments
        ]

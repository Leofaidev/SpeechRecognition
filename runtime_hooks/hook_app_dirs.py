"""PyInstaller runtime hook: redirect HuggingFace cache into the app directory."""
import os
import sys

if getattr(sys, "frozen", False):
    _app = os.path.dirname(os.path.abspath(sys.executable))
    _models = os.path.join(_app, "models")
    # Point HuggingFace Hub (pyannote, transformers, faster-whisper) to app dir.
    os.environ.setdefault("HF_HOME", _models)
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", os.path.join(_models, "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(_models, "hub"))

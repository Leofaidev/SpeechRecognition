"""Helpers for detecting and recovering from corrupted HuggingFace model caches.

Usage (in any engine that loads a HF model):

    try:
        model = load_fn()
    except Exception as exc:
        if not is_auth_or_network_error(exc):
            force_redownload(repo_id, token=token)
            model = load_fn()   # second attempt; raises if still broken
        else:
            raise
"""
from __future__ import annotations


def is_auth_or_network_error(exc: Exception) -> bool:
    """Return True for errors that a re-download cannot fix.

    Covers authentication/authorisation failures and transient network
    problems.  Corruption or truncation errors return False.
    """
    msg = str(exc).lower()
    return any(kw in msg for kw in (
        "401", "403", "gated", "access repository", "forbidden",
        "unauthorized", "authentication", "token", "password",
        "connection", "timeout", "network", "ssl", "cert",
        "name or service not known", "nodename nor servname provided",
    ))


def force_redownload(repo_id: str, token: str | None = None) -> None:
    """Force HuggingFace Hub to re-download *repo_id*, ignoring local cache.

    Silently swallows errors — the subsequent model-load attempt will
    surface any real problem (e.g. the repo doesn't exist).
    """
    try:
        from huggingface_hub import snapshot_download
        kw: dict = {"token": token} if token else {}
        snapshot_download(repo_id, force_download=True, **kw)
    except Exception:
        pass

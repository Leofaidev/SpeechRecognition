#!/usr/bin/env bash
# Launch Speech Recognition Program on Linux
# Usage: bash run-linux.sh [--cli ...]
set -e

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO/.venv-linux"

if [ ! -d "$VENV" ]; then
    echo "ERROR: .venv-linux not found. Run: bash scripts/setup-ubuntu.sh" >&2
    exit 1
fi

cd "$REPO/src"
PYTHONPATH="$REPO/platforms:$REPO/src" \
    "$VENV/bin/python" -m gui.app "$@"

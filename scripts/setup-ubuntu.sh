#!/usr/bin/env bash
# Speech Recognition Program — Ubuntu setup script
# Tested on Ubuntu 24.04 / 26.04 Desktop
# Run as the app user (not root); sudo will be invoked where needed.
#
# Usage:
#   bash scripts/setup-ubuntu.sh [--skip-cuda]
#
# Options:
#   --skip-cuda    Install CPU-only PyTorch (useful for VMware VMs without GPU passthrough)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_CUDA=0

for arg in "$@"; do
    [[ "$arg" == "--skip-cuda" ]] && SKIP_CUDA=1
done

echo "======================================================"
echo "  Speech Recognition Program — Ubuntu Setup"
echo "  Repo: $REPO_DIR"
echo "======================================================"

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
echo ""
echo "[1/6] Installing system packages…"
sudo apt-get update
sudo apt-get install -y \
    python3.12 python3.12-dev python3.12-venv python3-pip \
    portaudio19-dev \
    ffmpeg \
    vlc \
    libsm6 libxext6 libgl1 libglib2.0-0 \
    python3-tk \
    xclip \
    build-essential \
    git

# Add user to input group (for keyboard hotkeys without sudo)
if ! groups "$USER" | grep -q '\binput\b'; then
    echo "  Adding $USER to 'input' group (hotkeys — log out to activate)…"
    sudo usermod -aG input "$USER"
fi

# ---------------------------------------------------------------------------
# 2. Python virtual environment
# ---------------------------------------------------------------------------
echo ""
echo "[2/6] Creating virtual environment…"
VENV_DIR="$REPO_DIR/.venv-linux"
python3.12 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# ---------------------------------------------------------------------------
# 3. PyTorch
# ---------------------------------------------------------------------------
echo ""
echo "[3/6] Installing PyTorch…"
if [[ $SKIP_CUDA -eq 1 ]]; then
    echo "  CPU-only mode (--skip-cuda)"
    pip install torch==2.12.0 torchaudio==2.11.0 \
        --index-url https://download.pytorch.org/whl/cpu
else
    echo "  CUDA 12.6 build"
    pip install torch==2.12.0+cu126 torchaudio==2.11.0 \
        --index-url https://download.pytorch.org/whl/cu126
fi

# ---------------------------------------------------------------------------
# 4. App dependencies
# ---------------------------------------------------------------------------
echo ""
echo "[4/6] Installing Python dependencies…"
pip install \
    --extra-index-url https://download.pytorch.org/whl/cu126 \
    -r "$REPO_DIR/requirements-linux.txt"

# ---------------------------------------------------------------------------
# 5. Launch script
# ---------------------------------------------------------------------------
echo ""
echo "[5/6] Creating launch script…"
LAUNCH_SCRIPT="$REPO_DIR/run-linux.sh"
cat > "$LAUNCH_SCRIPT" <<EOF
#!/usr/bin/env bash
# Launch Speech Recognition Program on Linux
cd "$REPO_DIR/src"
PYTHONPATH="$REPO_DIR/platforms:$REPO_DIR/src" \\
    "$VENV_DIR/bin/python" -m gui.app "\$@"
EOF
chmod +x "$LAUNCH_SCRIPT"
echo "  Launch script: $LAUNCH_SCRIPT"

# ---------------------------------------------------------------------------
# 6. Desktop shortcut (optional)
# ---------------------------------------------------------------------------
echo ""
echo "[6/6] Creating desktop shortcut…"
DESKTOP_FILE="$HOME/.local/share/applications/SpeechRecognitionProgram.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Speech Recognition Program
Comment=Locally-executed GPU-accelerated speech recognition
Exec=$LAUNCH_SCRIPT
Icon=$REPO_DIR/assets/WSP.ico
Terminal=false
Categories=AudioVideo;Audio;
EOF
echo "  Desktop entry: $DESKTOP_FILE"

echo ""
echo "======================================================"
echo "  Setup complete!"
echo ""
echo "  To run the app:"
echo "    bash $LAUNCH_SCRIPT"
echo ""
echo "  To test the AI pipeline:"
echo "    source $VENV_DIR/bin/activate"
echo "    python $REPO_DIR/scripts/test_ai_pipeline.py --model tiny"
echo ""
if ! groups "$USER" | grep -q '\binput\b'; then
    echo "  NOTE: Log out and back in to activate hotkey support (input group)."
    echo ""
fi
echo "======================================================"

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

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_CUDA=0

for arg in "$@"; do
    [[ "$arg" == "--skip-cuda" ]] && SKIP_CUDA=1
done

# Pick the best available Python (3.12 preferred; fall back to 3.13, 3.14, system python3)
PYTHON_BIN=""
for v in python3.12 python3.13 python3.14 python3; do
    if command -v "$v" &>/dev/null; then
        PYTHON_BIN="$v"
        break
    fi
done
if [[ -z "$PYTHON_BIN" ]]; then
    echo "ERROR: no Python 3.x found" >&2; exit 1
fi
PY_VER=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Using Python: $PYTHON_BIN ($("$PYTHON_BIN" --version))"

echo "======================================================"
echo "  Speech Recognition Program — Ubuntu Setup"
echo "  Repo: $REPO_DIR"
echo "======================================================"

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
echo ""
echo "[1/6] Installing system packages…"
sudo apt-get update -q

# Core deps — always work
sudo apt-get install -y --no-install-recommends \
    python3-pip \
    python3-tk \
    python3-pyaudio \
    portaudio19-dev \
    ffmpeg \
    libsm6 libxext6 libgl1 libglib2.0-0t64 \
    xclip \
    build-essential \
    git

# Python version-specific packages — non-fatal if missing
# python${PY_VER}-tk  → tkinter in virtualenv when python3-tk targets a different minor version
# python${PY_VER}-dev → C headers for building pyaudio wheel
sudo apt-get install -y --no-install-recommends \
    "python${PY_VER}-tk" \
    "python${PY_VER}-dev" 2>/dev/null || \
    echo "  Warning: python${PY_VER}-tk/-dev not available; using python3-tk/-pyaudio system fallback"

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

# Ubuntu 26.04 PEP 668: system pip blocks installs without --break-system-packages
pip3 install --quiet --break-system-packages virtualenv
"$PYTHON_BIN" -m virtualenv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Upgrade pip inside the venv — --ignore-installed avoids failure when the
# venv inherits a Debian-managed pip with no RECORD file
pip install --upgrade pip --ignore-installed --quiet

# Make system pyaudio visible to the venv via a .pth file.
# python3-pyaudio (apt) installs to /usr/lib/python3/dist-packages/ which
# virtualenv isolates by default; the .pth re-adds it without --system-site-packages.
PYAUDIO_DIR=$(/usr/bin/python3 -c "import pyaudio, os; print(os.path.dirname(pyaudio.__file__))" 2>/dev/null || echo "")
if [[ -n "$PYAUDIO_DIR" ]]; then
    PARENT_DIR=$(dirname "$PYAUDIO_DIR")
    echo "$PARENT_DIR" > "$VENV_DIR/lib/python${PY_VER}/site-packages/system-pyaudio.pth"
    echo "  pyaudio available via pth: $PARENT_DIR"
fi

# ---------------------------------------------------------------------------
# 3. PyTorch  (separate install calls prevent pip from rolling both back on
#              a torchaudio version mismatch)
# ---------------------------------------------------------------------------
echo ""
echo "[3/6] Installing PyTorch…"
if [[ $SKIP_CUDA -eq 1 ]]; then
    echo "  CPU-only mode (--skip-cuda)"
    CPU_URL=https://download.pytorch.org/whl/cpu
    pip install torch==2.12.0+cpu    --index-url "$CPU_URL" --quiet
    pip install torchaudio==2.11.0+cpu --index-url "$CPU_URL" --quiet
else
    echo "  CUDA 12.6 build"
    CUDA_URL=https://download.pytorch.org/whl/cu126
    pip install torch==2.12.0+cu126    --index-url "$CUDA_URL" --quiet
    pip install torchaudio==2.11.0+cu126 --index-url "$CUDA_URL" --quiet
fi
python -c "import torch; print(f'  torch {torch.__version__} | CUDA: {torch.cuda.is_available()}')"

# ---------------------------------------------------------------------------
# 4. App dependencies
# ---------------------------------------------------------------------------
echo ""
echo "[4/6] Installing Python dependencies…"

# Build a filtered requirements file for this run
FILTERED_REQS=/tmp/wsp_reqs_filtered.txt
grep -v "^torch==" "$REPO_DIR/requirements-linux.txt" | \
    grep -v "^torchaudio==" | \
    grep -v "^torchcodec==" \
    > "$FILTERED_REQS"

if [[ $SKIP_CUDA -eq 1 ]]; then
    # Replace onnxruntime-gpu with the CPU version
    sed -i 's/^onnxruntime-gpu.*/onnxruntime/' "$FILTERED_REQS"
fi

TORCH_INDEX_URL=""
if [[ $SKIP_CUDA -eq 1 ]]; then
    TORCH_INDEX_URL="--extra-index-url https://download.pytorch.org/whl/cpu"
else
    TORCH_INDEX_URL="--extra-index-url https://download.pytorch.org/whl/cu126"
fi

pip install $TORCH_INDEX_URL -r "$FILTERED_REQS"

# ---------------------------------------------------------------------------
# 5. Launch script
# ---------------------------------------------------------------------------
echo ""
echo "[5/6] Creating launch script…"
LAUNCH_SCRIPT="$REPO_DIR/run-linux.sh"
cat > "$LAUNCH_SCRIPT" <<LAUNCH
#!/usr/bin/env bash
# Launch Speech Recognition Program on Linux
set -e
REPO="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$REPO/src"
PYTHONPATH="\$REPO/platforms:\$REPO/src" \\
    "$VENV_DIR/bin/python" -m gui.app "\$@"
LAUNCH
chmod +x "$LAUNCH_SCRIPT"
echo "  Launch script: $LAUNCH_SCRIPT"

# ---------------------------------------------------------------------------
# 6. Desktop shortcut (optional)
# ---------------------------------------------------------------------------
echo ""
echo "[6/6] Creating desktop shortcut…"
DESKTOP_FILE="$HOME/.local/share/applications/SpeechRecognitionProgram.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<DESKENTRY
[Desktop Entry]
Type=Application
Name=Speech Recognition Program
Comment=Locally-executed GPU-accelerated speech recognition
Exec=$LAUNCH_SCRIPT
Icon=$REPO_DIR/assets/WSP.ico
Terminal=false
Categories=AudioVideo;Audio;
DESKENTRY
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

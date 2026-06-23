#!/usr/bin/env bash
# ============================================================================
#  Speech Recognition Program — Ubuntu Installer  v1.0.0
#  Supports: Ubuntu 24.04 (Noble) / 26.04 (Resolute Raccoon) — x86_64
#
#  Usage:
#    bash wsp_installer_ubuntu.sh [options]
#
#  Options:
#    --no-cuda              CPU-only PyTorch (machines without NVIDIA GPU)
#    --yes, -y              Accept defaults and licence without prompting
#    --dir PATH             Override install directory (default: ~/SpeechRecognitionProgram)
#    --source-dir PATH      Use a local repo copy instead of downloading from GitHub
#    --existing-venv PATH   Use a pre-built venv; skip venv creation and pip install
#    --help, -h             Show this help and exit
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
_RED='\033[0;31m'; _YLW='\033[1;33m'; _GRN='\033[0;32m'
_BLD='\033[1m';    _DIM='\033[2m';     _NC='\033[0m'
info()    { echo -e "${_GRN}[WSP]${_NC} $*"; }
warn()    { echo -e "${_YLW}[WARN]${_NC} $*"; }
err()     { echo -e "${_RED}[ERROR]${_NC} $*" >&2; }
section() { echo -e "\n${_BLD}━━━  $*  ━━━${_NC}\n"; }
die()     { err "$*"; exit 1; }

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
APP_NAME="Speech Recognition Program"
APP_VERSION="1.0.0"
GITHUB_REPO="Leofaidev/SpeechRecognition"
SOURCE_URL="https://github.com/${GITHUB_REPO}/archive/refs/heads/master.tar.gz"

INSTALL_DIR="$HOME/SpeechRecognitionProgram"
NO_CUDA=0
YES_MODE=0
SOURCE_DIR=""
EXISTING_VENV=""

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-cuda)          NO_CUDA=1 ;;
        --yes|-y)           YES_MODE=1 ;;
        --dir)              INSTALL_DIR="$2"; shift ;;
        --dir=*)            INSTALL_DIR="${1#--dir=}" ;;
        --source-dir)       SOURCE_DIR="$2"; shift ;;
        --source-dir=*)     SOURCE_DIR="${1#--source-dir=}" ;;
        --existing-venv)    EXISTING_VENV="$2"; shift ;;
        --existing-venv=*)  EXISTING_VENV="${1#--existing-venv=}" ;;
        -h|--help)
            grep '^#  ' "$0" | sed 's/^#  //'
            exit 0 ;;
        *) warn "Unknown option: $1" ;;
    esac
    shift
done

# ---------------------------------------------------------------------------
# 0. Welcome banner
# ---------------------------------------------------------------------------
clear 2>/dev/null || true
echo -e "${_BLD}"
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║        Speech Recognition Program  v${APP_VERSION}         ║"
echo "  ║              Ubuntu Installer                        ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo -e "${_NC}"
echo "  This installer will:"
echo "    • Install system packages (apt)"
echo "    • Set up a Python virtual environment"
echo "    • Download Python libraries (3 – 8 GB depending on GPU mode)"
echo "    • Create a desktop shortcut and launcher"
echo ""
echo "  An internet connection is required."
echo ""

prompt() {
    # prompt "Question" default_value → reads answer, uses default if empty
    local msg="$1" def="${2:-}"
    if [[ $YES_MODE -eq 1 ]]; then
        echo "$def"; return
    fi
    local ans
    read -rp "  ${msg} [${def}]: " ans
    echo "${ans:-$def}"
}

yn() {
    # yn "Question" Y|N → returns 0 (yes) or 1 (no)
    local ans
    ans=$(prompt "$1" "$2")
    [[ "${ans,,}" == "y" ]]
}

# ---------------------------------------------------------------------------
# 1. System checks
# ---------------------------------------------------------------------------
section "System Check"

# OS
if ! grep -qi 'ubuntu' /etc/os-release 2>/dev/null; then
    OS_NAME=$(grep '^NAME=' /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "unknown")
    die "Ubuntu is required. Detected: $OS_NAME"
fi
UBUNTU_VER=$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
UBUNTU_MAJOR=$(echo "$UBUNTU_VER" | cut -d. -f1)
UBUNTU_MINOR=$(echo "$UBUNTU_VER" | cut -d. -f2)
if [[ $UBUNTU_MAJOR -lt 24 ]] || [[ $UBUNTU_MAJOR -eq 24 && $UBUNTU_MINOR -lt 4 ]]; then
    die "Ubuntu 24.04 or later is required. Detected: $UBUNTU_VER"
fi
info "Ubuntu $UBUNTU_VER — OK"

# Architecture
ARCH=$(uname -m)
[[ "$ARCH" != "x86_64" ]] && die "Only x86_64 is supported. Detected: $ARCH"
info "Architecture: $ARCH — OK"

# Internet (skip check when using a local source dir)
if [[ -z "$SOURCE_DIR" ]]; then
    if ! curl -s --connect-timeout 8 https://github.com >/dev/null 2>&1; then
        die "Cannot reach github.com. Check your internet connection."
    fi
    info "Internet connectivity — OK"
fi

# Disk space (15 GB recommended)
AVAIL_KB=$(df --output=avail "$HOME" | tail -1 | tr -d ' ')
AVAIL_GB=$(( AVAIL_KB / 1024 / 1024 ))
info "Available disk space: ${AVAIL_GB} GB"
[[ $AVAIL_GB -lt 15 ]] && \
    warn "Less than 15 GB free. Installation may fail if disk fills up."

# NVIDIA GPU
HAVE_GPU=0
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    info "NVIDIA GPU: $GPU_NAME"
    HAVE_GPU=1
else
    info "No NVIDIA GPU detected — will use CPU-only mode."
    NO_CUDA=1
fi

# Python (prefer 3.12, accept 3.13 / 3.14)
PYTHON_BIN=""
for _v in python3.12 python3.13 python3.14 python3; do
    if command -v "$_v" &>/dev/null; then
        PYTHON_BIN="$_v"; break
    fi
done
[[ -z "$PYTHON_BIN" ]] && die "Python 3 not found. Run: sudo apt install python3"
PY_VER=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python: $("$PYTHON_BIN" --version)"

# ---------------------------------------------------------------------------
# 2. HuggingFace licence
# ---------------------------------------------------------------------------
section "Speaker Diarisation — HuggingFace Licence"
cat <<'EOF'
  Speaker identification (pyannote.audio models) requires a free HuggingFace
  account and acceptance of the model licence at:

    https://huggingface.co/pyannote/speaker-diarization-3.1
    https://huggingface.co/pyannote/segmentation-3.0

  After installation, enter your HuggingFace token in the application's
  AI Config panel to activate speaker diarisation.

  Without a token, all speakers are labelled "Unknown" — all other features
  work normally.

EOF

if yn "Do you understand and accept the HuggingFace licence terms?" "Y"; then
    HF_ACCEPTED=true
    info "HuggingFace licence accepted."
else
    HF_ACCEPTED=false
    warn "Skipped — speaker diarisation will be disabled until a token is provided."
fi

# ---------------------------------------------------------------------------
# 3. Installation path
# ---------------------------------------------------------------------------
section "Installation Directory"
echo "  The application will be installed in a self-contained directory."
echo "  The directory will be created if it does not exist."
echo ""
INSTALL_DIR=$(prompt "Install to" "$INSTALL_DIR")
INSTALL_DIR="${INSTALL_DIR%/}"   # strip trailing slash

if [[ -d "$INSTALL_DIR" && -n "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]]; then
    warn "Directory is not empty: $INSTALL_DIR"
    yn "Overwrite existing files?" "Y" || die "Installation cancelled."
fi

# ---------------------------------------------------------------------------
# 4. GPU / CPU mode
# ---------------------------------------------------------------------------
if [[ $HAVE_GPU -eq 1 && $NO_CUDA -eq 0 && $YES_MODE -eq 0 ]]; then
    section "Processing Mode"
    echo "  An NVIDIA GPU was detected. GPU mode is strongly recommended:"
    echo "    GPU (CUDA)  — fastest transcription, uses VRAM"
    echo "    CPU only    — slower; works without a GPU or with small models"
    echo ""
    if ! yn "Use GPU (CUDA) mode?" "Y"; then
        NO_CUDA=1
    fi
fi

[[ $NO_CUDA -eq 1 ]] && TORCH_MODE="CPU-only" || TORCH_MODE="CUDA (GPU)"

# ---------------------------------------------------------------------------
# Summary + confirmation
# ---------------------------------------------------------------------------
section "Installation Summary"
echo "  Application  : $APP_NAME v$APP_VERSION"
echo "  Install path : $INSTALL_DIR"
echo "  PyTorch mode : $TORCH_MODE"
echo "  HF licence   : $([[ $HF_ACCEPTED == true ]] && echo 'Accepted' || echo 'Skipped')"
echo ""
yn "Proceed with installation?" "Y" || die "Installation cancelled."

# ---------------------------------------------------------------------------
# 5. System packages
# ---------------------------------------------------------------------------
section "Step 1/7 — System Packages (apt)"
info "Updating package index…"
sudo apt-get update -q

PKGS=(
    python3-pip python3-tk python3-pyaudio portaudio19-dev
    ffmpeg vlc
    libsm6 libxext6 libgl1
    xclip build-essential curl git
)
info "Installing: ${PKGS[*]}"
sudo apt-get install -y --no-install-recommends "${PKGS[@]}"

# libglib2.0-0 was renamed to libglib2.0-0t64 on Ubuntu 26.04
sudo apt-get install -y --no-install-recommends libglib2.0-0t64 2>/dev/null \
    || sudo apt-get install -y --no-install-recommends libglib2.0-0 2>/dev/null \
    || warn "libglib2.0 not found — OpenCV may fail to load."

# Python version-specific packages (non-fatal if unavailable)
sudo apt-get install -y --no-install-recommends \
    "python${PY_VER}-tk" "python${PY_VER}-dev" 2>/dev/null \
    || warn "python${PY_VER}-tk/-dev not available; using system python3-tk fallback."

# Global hotkeys: user must be in the 'input' group
if ! groups "$USER" | grep -q '\binput\b'; then
    info "Adding $USER to 'input' group (for global hotkeys — takes effect after logout)."
    sudo usermod -aG input "$USER"
fi

# ---------------------------------------------------------------------------
# 6. Download / copy source
# ---------------------------------------------------------------------------
section "Step 2/7 — Application Source"
mkdir -p "$INSTALL_DIR"

if [[ -n "$SOURCE_DIR" ]]; then
    # Developer / offline mode: copy from a local repo
    info "Using local source: $SOURCE_DIR"
    rsync -a --delete \
        --exclude='.venv*' --exclude='.git' --exclude='__pycache__' \
        --exclude='*.pyc' --exclude='.pytest_cache' --exclude='.mypy_cache' \
        --exclude='installer/Output/' --exclude='*.egg-info' \
        "${SOURCE_DIR%/}/" "$INSTALL_DIR/"
else
    TMPTAR=$(mktemp /tmp/wsp_src_XXXXXX.tar.gz)
    info "Downloading source from GitHub…"
    curl -L --progress-bar "$SOURCE_URL" -o "$TMPTAR"
    TMPEXT=$(mktemp -d /tmp/wsp_src_XXXXXX)
    info "Extracting…"
    tar -xzf "$TMPTAR" -C "$TMPEXT" --strip-components=1
    rm -f "$TMPTAR"
    rsync -a --delete \
        --exclude='.venv*' --exclude='.git' --exclude='__pycache__' \
        --exclude='*.pyc' --exclude='.pytest_cache' --exclude='.mypy_cache' \
        --exclude='installer/Output/' --exclude='*.egg-info' \
        "$TMPEXT/" "$INSTALL_DIR/"
    rm -rf "$TMPEXT"
fi
info "Source ready at: $INSTALL_DIR"

# ---------------------------------------------------------------------------
# 7. Python virtual environment
# ---------------------------------------------------------------------------
section "Step 3/7 — Python Virtual Environment"

if [[ -n "$EXISTING_VENV" ]]; then
    VENV_DIR="$EXISTING_VENV"
    [[ -x "$VENV_DIR/bin/python" ]] || die "--existing-venv: no python binary at $VENV_DIR/bin/python"
    info "Using existing venv: $VENV_DIR"
else
    VENV_DIR="$INSTALL_DIR/.venv-linux"

    # Ubuntu 26.04 PEP 668: system pip blocks installs without --break-system-packages
    pip3 install --quiet --break-system-packages virtualenv 2>/dev/null \
        || pip3 install --quiet virtualenv
    "$PYTHON_BIN" -m virtualenv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip --ignore-installed --quiet
    info "Virtualenv created: $VENV_DIR"

    # Bridge python3-pyaudio (apt) into the venv via a .pth file.
    # python3-pyaudio installs to /usr/lib/python3/dist-packages/ which
    # virtualenv isolates; the pth re-adds it without --system-site-packages.
    PYAUDIO_PARENT=$(/usr/bin/python3 -c \
        "import pyaudio, os; print(os.path.dirname(os.path.dirname(pyaudio.__file__)))" \
        2>/dev/null || echo "")
    if [[ -n "$PYAUDIO_PARENT" ]]; then
        echo "$PYAUDIO_PARENT" \
            > "$VENV_DIR/lib/python${PY_VER}/site-packages/system-pyaudio.pth"
        info "pyaudio bridge → $PYAUDIO_PARENT"
    fi
fi

# ---------------------------------------------------------------------------
# 8. PyTorch
# ---------------------------------------------------------------------------
if [[ -z "$EXISTING_VENV" ]]; then
    section "Step 4/7 — PyTorch"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    if [[ $NO_CUDA -eq 1 ]]; then
        info "Installing CPU-only PyTorch (torch 2.12.0, torchaudio 2.11.0)…"
        CPU_URL="https://download.pytorch.org/whl/cpu"
        pip install "torch==2.12.0+cpu"      --index-url "$CPU_URL"
        pip install "torchaudio==2.11.0+cpu" --index-url "$CPU_URL"
    else
        info "Installing CUDA 12.6 PyTorch (torch 2.12.0, torchaudio 2.11.0)…"
        CUDA_URL="https://download.pytorch.org/whl/cu126"
        pip install "torch==2.12.0+cu126"      --index-url "$CUDA_URL"
        pip install "torchaudio==2.11.0+cu126" --index-url "$CUDA_URL"
    fi
    python -c "import torch; print(f'  torch {torch.__version__} | CUDA available: {torch.cuda.is_available()}')"
else
    section "Step 4/7 — PyTorch"
    info "Skipped (existing venv)."
fi

# ---------------------------------------------------------------------------
# 9. App Python libraries
# ---------------------------------------------------------------------------
if [[ -z "$EXISTING_VENV" ]]; then
    section "Step 5/7 — Python Libraries"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    REQS="$INSTALL_DIR/requirements-linux.txt"
    [[ -f "$REQS" ]] || die "requirements-linux.txt not found in $INSTALL_DIR"

    FILTERED=$(mktemp /tmp/wsp_reqs_XXXXXX.txt)
    trap 'rm -f "$FILTERED"' EXIT

    # Torch packages already installed above; torchcodec wheels unavailable on Linux
    grep -v '^torch==' "$REQS" \
        | grep -v '^torchaudio==' \
        | grep -v '^torchcodec==' \
        > "$FILTERED"

    if [[ $NO_CUDA -eq 1 ]]; then
        sed -i 's/^onnxruntime-gpu.*/onnxruntime/' "$FILTERED"
        EXTRA_IDX="--extra-index-url https://download.pytorch.org/whl/cpu"
    else
        EXTRA_IDX="--extra-index-url https://download.pytorch.org/whl/cu126"
    fi

    pip install $EXTRA_IDX -r "$FILTERED"
    info "Python libraries installed."
else
    section "Step 5/7 — Python Libraries"
    info "Skipped (existing venv)."
fi

# ---------------------------------------------------------------------------
# 10. Launcher script
# ---------------------------------------------------------------------------
section "Step 6/7 — Launcher & Desktop Entry"
LAUNCHER="$INSTALL_DIR/run-linux.sh"
cat > "$LAUNCHER" <<LAUNCH
#!/usr/bin/env bash
# Speech Recognition Program — Linux launcher
set -e
REPO="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="\$REPO/platforms:\$REPO/src"
cd "\$REPO/src"
exec "${VENV_DIR}/bin/python" -m gui.app "\$@"
LAUNCH
chmod +x "$LAUNCHER"
info "Launcher: $LAUNCHER"

# System-wide command 'wsp' (best effort; skip if no write permission)
if sudo ln -sf "$LAUNCHER" /usr/local/bin/wsp 2>/dev/null; then
    info "Command installed: wsp"
fi

# ---------------------------------------------------------------------------
# 11. Desktop entry
# ---------------------------------------------------------------------------
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$APPS_DIR" "$ICONS_DIR"

ICON_SRC="$INSTALL_DIR/assets/WSP.png"
ICON_DEST="$ICONS_DIR/SpeechRecognitionProgram.png"
if [[ -f "$ICON_SRC" ]]; then
    cp "$ICON_SRC" "$ICON_DEST"
    info "Icon: $ICON_DEST"
else
    ICON_DEST="application-x-executable"
fi

DESKTOP="$APPS_DIR/SpeechRecognitionProgram.desktop"
cat > "$DESKTOP" <<DESKENTRY
[Desktop Entry]
Type=Application
Name=Speech Recognition Program
GenericName=Speech Recognition
Comment=Locally-executed GPU-accelerated speech recognition
Exec=${LAUNCHER}
Icon=${ICON_DEST}
Terminal=false
Categories=AudioVideo;Audio;Utility;
Keywords=speech;voice;transcription;recognition;whisper;
StartupNotify=true
DESKENTRY
chmod 644 "$DESKTOP"
update-desktop-database "$APPS_DIR" 2>/dev/null || true
info "Desktop entry: $DESKTOP"

# ---------------------------------------------------------------------------
# 12. Initial config
# ---------------------------------------------------------------------------
section "Step 7/7 — Initial Configuration"
CFG_DIR="$HOME/.local/share/SpeechRecognition"
CFG_FILE="$CFG_DIR/config.json"
mkdir -p "$CFG_DIR"
if [[ ! -f "$CFG_FILE" ]]; then
    cat > "$CFG_FILE" <<CFG
{
  "licence_accepted": ${HF_ACCEPTED},
  "whisper_model": "small"
}
CFG
    info "Config written: $CFG_FILE"
else
    info "Existing config kept: $CFG_FILE"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${_GRN}${_BLD}  ╔══════════════════════════════════════════════════════╗"
echo "  ║   Installation complete!                             ║"
echo -e "  ╚══════════════════════════════════════════════════════╝${_NC}"
echo ""
echo "  To launch the application:"
echo -e "  ${_DIM}•${_NC} Applications menu  →  Speech Recognition Program"
if [[ -L /usr/local/bin/wsp ]]; then
echo -e "  ${_DIM}•${_NC} Terminal: ${_BLD}wsp${_NC}"
fi
echo -e "  ${_DIM}•${_NC} Terminal: ${_BLD}bash ${LAUNCHER}${_NC}"
echo ""

if ! groups "$USER" | grep -q '\binput\b'; then
    echo -e "  ${_YLW}NOTE:${_NC} Log out and back in for global hotkeys to take effect."
    echo "        (The installer added your account to the 'input' group.)"
    echo ""
fi

if [[ $HF_ACCEPTED == true ]]; then
    echo "  To enable speaker diarisation:"
    echo "    Open AI Config panel → enter your HuggingFace token."
    echo ""
fi

echo -e "${_DIM}  Models (Whisper / pyannote) are downloaded on first use.${_NC}"
echo ""

if yn "Launch Speech Recognition Program now?" "Y"; then
    info "Launching…"
    nohup bash "$LAUNCHER" >/dev/null 2>&1 &
    disown
fi

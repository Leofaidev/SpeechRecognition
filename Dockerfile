# Speech Recognition Program — Docker image for AI pipeline testing
# Base: Ubuntu 24.04 + CUDA 12.6 (matches Windows CUDA version)
#
# Build:
#   docker build -t wsp-test .
#
# Run (GPU):
#   docker run --gpus all --rm -it wsp-test
#
# Run (CPU-only):
#   docker run --rm -it wsp-test

FROM nvidia/cuda:12.6.0-base-ubuntu24.04

# Prevent interactive prompts during apt
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies (vlc/curl omitted — their deps hit transient 503s; not needed for AI test)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3-pip \
    python3.12-venv \
    portaudio19-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Make python3.12 the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Upgrade pip (--ignore-installed avoids failure on Debian-managed pip with no RECORD file)
RUN python3 -m pip install --upgrade pip --break-system-packages --ignore-installed

# Install PyTorch with CUDA 12.6 first (separate step for caching)
RUN python3 -m pip install --break-system-packages \
    torch==2.12.0+cu126 \
    torchaudio==2.11.0 \
    --index-url https://download.pytorch.org/whl/cu126

# Copy requirements and install (excluding Windows-only packages)
COPY requirements-linux.txt /tmp/requirements-linux.txt
RUN python3 -m pip install --break-system-packages \
    --extra-index-url https://download.pytorch.org/whl/cu126 \
    -r /tmp/requirements-linux.txt

# Copy application source
WORKDIR /app
COPY . .

# Add platforms/ and src/ to PYTHONPATH
ENV PYTHONPATH="/app/platforms:/app/src"

# Default: run the pipeline test
CMD ["python3", "scripts/test_ai_pipeline.py"]

#!/bin/bash
# Install Real-ESRGAN, Waifu2x, and Dandere2x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PLUGIN_PATH="$(dirname "$SCRIPT_DIR")"
PLUGIN_ID="$(basename "$PLUGIN_PATH")"

UNMANIC_BASE="$(cd "$(dirname "$(dirname "$PLUGIN_PATH")")" && pwd)"
USERDATA_PATH="$UNMANIC_BASE/userdata"

REALESRGAN_RELEASE="v0.2.5.0"
REALESRGAN_VERSION="20220424"
WAIFU2X_VERSION="20220728"
DANDERE2X_COMMIT="95f6766214a12855f0f0c73b3a327e43f71a33c8"

LOCAL_BASE="$USERDATA_PATH/$PLUGIN_ID"
LOCAL_BIN_DIR="$LOCAL_BASE/bin"
LOCAL_SHARE_DIR="$LOCAL_BASE/share"
mkdir -p "$LOCAL_BIN_DIR" "$LOCAL_SHARE_DIR"

REALESRGAN_SHARE_BASE="$LOCAL_SHARE_DIR/realesrgan-ncnn-vulkan"
REALESRGAN_SHARE_DIR="$REALESRGAN_SHARE_BASE/realesrgan-ncnn-vulkan-$REALESRGAN_VERSION"
REALESRGAN_BIN="$LOCAL_BIN_DIR/realesrgan-ncnn-vulkan"
REALESRGAN_URL="https://github.com/xinntao/Real-ESRGAN/releases/download/${REALESRGAN_RELEASE}/realesrgan-ncnn-vulkan-${REALESRGAN_VERSION}-ubuntu.zip"

WAIFU2X_SHARE_BASE="$LOCAL_SHARE_DIR/waifu2x-ncnn-vulkan"
WAIFU2X_SHARE_DIR="$WAIFU2X_SHARE_BASE/waifu2x-ncnn-vulkan-$WAIFU2X_VERSION"
WAIFU2X_BIN="$LOCAL_BIN_DIR/waifu2x-ncnn-vulkan"
WAIFU2X_URL="https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/${WAIFU2X_VERSION}/waifu2x-ncnn-vulkan-${WAIFU2X_VERSION}-ubuntu.zip"

DANDERE2X_SHARE_BASE="$LOCAL_SHARE_DIR/dandere2x"
DANDERE2X_SOURCE_DIR="$DANDERE2X_SHARE_BASE/dandere2x"
DANDERE2X_VENV_DIR="$DANDERE2X_SHARE_BASE/venv"
DANDERE2X_BIN="$LOCAL_BIN_DIR/dandere2x"
PY38_DIR="$LOCAL_SHARE_DIR/python38"
PY38_PREFIX="$PY38_DIR/python"
PY38_VERSION="3.8.18+20240107"
PY38_TARBALL="cpython-${PY38_VERSION}-x86_64-unknown-linux-gnu-install_only.tar.gz"
PY38_URL="https://github.com/indygreg/python-build-standalone/releases/download/20240107/${PY38_TARBALL}"
PY38_BIN="$PY38_PREFIX/bin/python3.8"

mkdir -p "$LOCAL_BIN_DIR" "$LOCAL_SHARE_DIR"
mkdir -p "$REALESRGAN_SHARE_BASE" "$WAIFU2X_SHARE_BASE" "$DANDERE2X_SHARE_BASE"

# -----------------------------------------------------------------------------
# Dependency Check
# -----------------------------------------------------------------------------
echo "Checking dependencies..."
MISSING_DEPS=false
if ! command -v unzip &>/dev/null; then MISSING_DEPS=true; fi
if ! command -v git &>/dev/null; then MISSING_DEPS=true; fi
if ! dpkg -s libvulkan1 &>/dev/null; then MISSING_DEPS=true; fi
if ! dpkg -s mesa-vulkan-drivers &>/dev/null; then MISSING_DEPS=true; fi
if ! command -v cmake &>/dev/null; then MISSING_DEPS=true; fi
if ! command -v g++ &>/dev/null; then MISSING_DEPS=true; fi

if [ "$MISSING_DEPS" = true ]; then
    if [ "$(id -u)" -eq 0 ]; then
        echo "Installing missing dependencies..."
        [[ "${__apt_updated:-false}" == 'false' ]] && apt-get update && __apt_updated=true
        # Install runtime deps
        apt-get install -y \
            libvulkan1 \
            mesa-vulkan-drivers \
            python3-pip
        # Install build deps
        apt-get install -y \
            build-essential \
            cmake \
            git \
            libjpeg-dev \
            libpng-dev \
            libtiff-dev \
            libwebp-dev \
            unzip \
            zlib1g-dev
    else
        echo "WARNING: Not running as root. Dependencies might be missing."
    fi
fi

# -----------------------------------------------------------------------------
# Standalone Python 3.8 Installation
# -----------------------------------------------------------------------------
if [ ! -x "$PY38_BIN" ]; then
    echo "Installing standalone Python 3.8 into $PY38_DIR..."
    rm -f "$PY38_DIR/.installed"
    mkdir -p "$PY38_DIR"
    wget -qO "$PY38_DIR/$PY38_TARBALL" "$PY38_URL"
    tar -xzf "$PY38_DIR/$PY38_TARBALL" -C "$PY38_DIR"
    rm -f "$PY38_DIR/$PY38_TARBALL"
    echo "$PY38_VERSION" > "$PY38_DIR/.installed"
fi

# -----------------------------------------------------------------------------
# Real-ESRGAN Installation
# -----------------------------------------------------------------------------
echo "Checking Real-ESRGAN..."
REALESRGAN_INSTALLED_VERSION=""
if [ -f "$REALESRGAN_SHARE_BASE/.installed" ]; then
    REALESRGAN_INSTALLED_VERSION=$(cat "$REALESRGAN_SHARE_BASE/.installed")
fi

if [ "$REALESRGAN_INSTALLED_VERSION" != "$REALESRGAN_VERSION" ]; then
    echo "Downloading Real-ESRGAN..."
    wget -qO /tmp/realesrgan.zip "$REALESRGAN_URL"
    unzip -o /tmp/realesrgan.zip -d /tmp/realesrgan
    mkdir -p "$REALESRGAN_SHARE_DIR"
    mv /tmp/realesrgan/realesrgan-ncnn-vulkan "$REALESRGAN_SHARE_DIR/"
    chmod +x "$REALESRGAN_SHARE_DIR/realesrgan-ncnn-vulkan"
    [ -d "$REALESRGAN_SHARE_DIR/models" ] && rm -rf "$REALESRGAN_SHARE_DIR/models"
    mv /tmp/realesrgan/models "$REALESRGAN_SHARE_DIR/"
    rm -rf /tmp/realesrgan /tmp/realesrgan.zip
    
    # Mark installation as complete
    echo "$REALESRGAN_VERSION" > "$REALESRGAN_SHARE_BASE/.installed"
else
    echo "Real-ESRGAN installed."
fi

ln -sf "$REALESRGAN_SHARE_DIR/realesrgan-ncnn-vulkan" "$REALESRGAN_BIN"

# -----------------------------------------------------------------------------
# Waifu2x Installation
# -----------------------------------------------------------------------------
echo "Checking Waifu2x..."
WAIFU2X_INSTALLED_VERSION=""
if [ -f "$WAIFU2X_SHARE_BASE/.installed" ]; then
    WAIFU2X_INSTALLED_VERSION=$(cat "$WAIFU2X_SHARE_BASE/.installed")
fi

if [ "$WAIFU2X_INSTALLED_VERSION" != "$WAIFU2X_VERSION" ]; then
    echo "Downloading Waifu2x..."
    wget -qO /tmp/waifu2x.zip "$WAIFU2X_URL"
    unzip -o /tmp/waifu2x.zip -d /tmp/waifu2x
    EXTRACTED_DIR=$(find /tmp/waifu2x -maxdepth 1 -mindepth 1 -type d | head -n 1)
    mkdir -p "$WAIFU2X_SHARE_DIR"
    mv "$EXTRACTED_DIR/waifu2x-ncnn-vulkan" "$WAIFU2X_SHARE_DIR/"
    chmod +x "$WAIFU2X_SHARE_DIR/waifu2x-ncnn-vulkan"
    mv "$EXTRACTED_DIR"/models-* "$WAIFU2X_SHARE_DIR/"
    rm -rf /tmp/waifu2x /tmp/waifu2x.zip
    
    # Mark installation as complete
    echo "$WAIFU2X_VERSION" > "$WAIFU2X_SHARE_BASE/.installed"
else
    echo "Waifu2x installed."
fi

ln -sf "$WAIFU2X_SHARE_DIR/waifu2x-ncnn-vulkan" "$WAIFU2X_BIN"

# -----------------------------------------------------------------------------
# Dandere2x Installation
# -----------------------------------------------------------------------------
echo "Checking Dandere2x..."

INSTALLED_VERSION=""
if [ -f "$DANDERE2X_SHARE_BASE/.installed" ]; then
    INSTALLED_VERSION=$(cat "$DANDERE2X_SHARE_BASE/.installed")
fi

if [ "$INSTALLED_VERSION" != "$DANDERE2X_COMMIT" ]; then
    echo "Installing Dandere2x (Commit: $DANDERE2X_COMMIT)..."

    # Clean previous source if it exists
    if [ -d "$DANDERE2X_SOURCE_DIR" ]; then
        rm -rf "$DANDERE2X_SOURCE_DIR"
    fi
    mkdir -p "$DANDERE2X_SHARE_BASE"

    echo "Cloning Dandere2x..."
    git clone https://github.com/akai-katto/dandere2x.git "$DANDERE2X_SOURCE_DIR"
    
    cd "$DANDERE2X_SOURCE_DIR"
    echo "Checking out commit $DANDERE2X_COMMIT..."
    git checkout "$DANDERE2X_COMMIT"

    # NOTE: This was used to unpin PyYAML because 5.4 fails to build on Py3.10+.
    # We now install Dandere2x with a standalone Python 3.8, so the patch is not needed.
    # echo "Patching requirements.txt..."
    # if [ -f "$DANDERE2X_SOURCE_DIR/src/requirements.txt" ]; then
    #     sed -i 's/pyyaml==5.4/PyYAML/g' "$DANDERE2X_SOURCE_DIR/src/requirements.txt"
    # fi

    # Patch for GCC 13+ support (missing <cstdint>)
    echo "Patching Block.cpp for GCC 13+..."
    BLOCK_CPP="$DANDERE2X_SOURCE_DIR/dandere2x_cpp/plugins/block_plugins/Block.cpp"
    if [ -f "$BLOCK_CPP" ]; then
        sed -i '27i#include <cstdint>' "$BLOCK_CPP"
    else
        echo "Error: Block.cpp not found at $BLOCK_CPP"
        exit 1
    fi

    # Create venv
    echo "Setting up Dandere2x venv..."
    "$PY38_BIN" -m venv "$DANDERE2X_VENV_DIR" --clear

    source "$DANDERE2X_VENV_DIR/bin/activate"
    
    # Update pip and install build dependencies
    "$DANDERE2X_VENV_DIR/bin/python3" -m pip install --upgrade pip setuptools wheel

    # Install requirements
    if ! "$DANDERE2X_VENV_DIR/bin/python3" -m pip install -r "$DANDERE2X_SOURCE_DIR/src/requirements.txt"; then
        echo "Failed to install Python requirements."
        exit 1
    fi

    # Run setup script to download its internal binaries and compile
    cd "$DANDERE2X_SOURCE_DIR/src"

    # Build dandere2x_cpp manually (replaces unix_setup.sh to avoid broken downloads)
    echo "Building dandere2x_cpp..."
    cd ../dandere2x_cpp
    cmake CMakeLists.txt
    make
    
    if [ ! -f "dandere2x_cpp" ]; then
        echo "Failed to build dandere2x_cpp"
        exit 1
    fi

    # Prepare externals directory
    cd ../src
    mkdir -p externals
    mv ../dandere2x_cpp/dandere2x_cpp ./externals/

    EXTERNALS_DIR="$DANDERE2X_SOURCE_DIR/src/externals"

    # Download RealSR (required by Dandere2x)
    echo "Installing RealSR for Dandere2x..."
    REALSR_VERSION="20220728"
    REALSR_URL="https://github.com/nihui/realsr-ncnn-vulkan/releases/download/${REALSR_VERSION}/realsr-ncnn-vulkan-${REALSR_VERSION}-ubuntu.zip"
    
    wget -qO /tmp/realsr.zip "$REALSR_URL"
    unzip -o /tmp/realsr.zip -d /tmp/realsr
    EXTRACTED_REALSR=$(find /tmp/realsr -maxdepth 1 -mindepth 1 -type d | head -n 1)
    mkdir -p "$EXTERNALS_DIR/realsr-ncnn-vulkan"
    mv "$EXTRACTED_REALSR"/* "$EXTERNALS_DIR/realsr-ncnn-vulkan/"
    chmod +x "$EXTERNALS_DIR/realsr-ncnn-vulkan/realsr-ncnn-vulkan"
    rm -rf /tmp/realsr /tmp/realsr.zip

    # Fix missing waifu2x in externals if download failed (common issue)
    if [ ! -d "$EXTERNALS_DIR/waifu2x-ncnn-vulkan" ]; then
        echo "Manually linking Waifu2x for Dandere2x..."
        mkdir -p "$EXTERNALS_DIR/waifu2x-ncnn-vulkan"
        # Link binary
        ln -sf "$WAIFU2X_BIN" "$EXTERNALS_DIR/waifu2x-ncnn-vulkan/waifu2x-ncnn-vulkan"
        # Link models
        for d in "$WAIFU2X_SHARE_DIR"/models-*; do
            if [ -d "$d" ]; then
                ln -sf "$d" "$EXTERNALS_DIR/waifu2x-ncnn-vulkan/"
            fi
        done
    fi
    
    # Create workspace directory
    cd ..
    mkdir -p workspace

    # Mark installation as complete
    echo "$DANDERE2X_COMMIT" > "$DANDERE2X_SHARE_BASE/.installed"

    deactivate
    echo "Dandere2x setup complete."
else
    echo "Dandere2x installed (Commit: $INSTALLED_VERSION)."
fi

cat <<'EOF' >"$DANDERE2X_BIN"
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="$BASE_DIR/share/dandere2x"
SOURCE_DIR="$INSTALL_DIR/dandere2x"
VENV_DIR="$INSTALL_DIR/venv"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Dandere2x not installed at $SOURCE_DIR" >&2
    exit 1
fi

source "$VENV_DIR/bin/activate"
exec "$VENV_DIR/bin/python3" "$SOURCE_DIR/src/main.py" "$@"
EOF
chmod +x "$DANDERE2X_BIN"

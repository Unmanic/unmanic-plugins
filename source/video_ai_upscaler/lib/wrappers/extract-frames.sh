#!/bin/bash
set -e

# Arguments
INPUT_FILE="$1"
FRAMES_IN_DIR="$2"

if [ -z "$INPUT_FILE" ] || [ -z "$FRAMES_IN_DIR" ]; then
    echo "Usage: extract-frames.sh INPUT_FILE FRAMES_IN_DIR" >&2
    exit 1
fi

mkdir -p "$FRAMES_IN_DIR"

echo "Extracting frames..."
ffmpeg -hide_banner -loglevel info -i "$INPUT_FILE" "$FRAMES_IN_DIR/%08d.png"

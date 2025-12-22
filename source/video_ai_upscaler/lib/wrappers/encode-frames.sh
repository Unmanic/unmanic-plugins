#!/bin/bash
set -e

# Arguments
FRAMES_OUT_DIR="$1"
INPUT_FILE="$2"
OUTPUT_FILE="$3"
TARGET_HEIGHT="$4"
ENCODING_ARGS="$5"

if [ -z "$FRAMES_OUT_DIR" ] || [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ] || [ -z "$TARGET_HEIGHT" ]; then
    echo "Usage: encode-frames.sh FRAMES_OUT_DIR INPUT_FILE OUTPUT_FILE TARGET_HEIGHT ENCODING_ARGS" >&2
    exit 1
fi

echo "Encoding output..."

FRAMERATE=$(ffmpeg -i "$INPUT_FILE" 2>&1 | sed -n "s/.*, \(.*\) fps.*/\1/p" | head -n 1)
if [ -z "$FRAMERATE" ]; then
    FRAMERATE="30"
fi

ffmpeg -hide_banner -loglevel info -y \
    -f image2 -framerate "$FRAMERATE" -i "$FRAMES_OUT_DIR/%08d.png" \
    -i "$INPUT_FILE" \
    -map 0:v -map 1:a? -map 1:s? \
    $ENCODING_ARGS \
    -vf "scale=-2:$TARGET_HEIGHT" \
    -c:a copy -c:s copy \
    "$OUTPUT_FILE"

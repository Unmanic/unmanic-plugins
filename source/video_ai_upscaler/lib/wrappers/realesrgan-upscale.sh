#!/bin/bash
set -e

# Arguments
REALESRGAN_BIN="$1"
FRAMES_IN_DIR="$2"
FRAMES_OUT_DIR="$3"
MODEL_NAME="$4"
SCALE="$5"
GPU_ARG="$6"
TILE_SIZE="$7"

if [ -z "$REALESRGAN_BIN" ] || [ -z "$FRAMES_IN_DIR" ] || [ -z "$FRAMES_OUT_DIR" ] || [ -z "$MODEL_NAME" ] || [ -z "$SCALE" ]; then
    echo "Usage: realesrgan-upscale.sh BIN FRAMES_IN_DIR FRAMES_OUT_DIR MODEL_NAME SCALE GPU_ARG TILE_SIZE" >&2
    exit 1
fi

mkdir -p "$FRAMES_OUT_DIR"

echo "Upscaling frames (this may take a while)..."
CMD="$REALESRGAN_BIN -i $FRAMES_IN_DIR -o $FRAMES_OUT_DIR -n $MODEL_NAME -s $SCALE -f png"
if [ -n "$GPU_ARG" ]; then
    CMD="$CMD $GPU_ARG"
fi

# Add tile size if specified and > 0
if [ -n "$TILE_SIZE" ] && [ "$TILE_SIZE" -gt 0 ]; then
    CMD="$CMD -t $TILE_SIZE"
fi

echo "Running: $CMD"
$CMD
echo "Done."

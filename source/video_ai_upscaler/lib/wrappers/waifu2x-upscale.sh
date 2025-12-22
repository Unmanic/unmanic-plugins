#!/bin/bash
set -e

# Arguments
WAIFU2X_BIN="$1"
FRAMES_IN_DIR="$2"
FRAMES_OUT_DIR="$3"
MODEL_PATH="$4"
SCALE="$5"
NOISE_LEVEL="$6"
GPU_ARG="$7"
TILE_SIZE="$8"

if [ -z "$WAIFU2X_BIN" ] || [ -z "$FRAMES_IN_DIR" ] || [ -z "$FRAMES_OUT_DIR" ] || [ -z "$MODEL_PATH" ] || [ -z "$SCALE" ]; then
    echo "Usage: waifu2x-upscale.sh BIN FRAMES_IN_DIR FRAMES_OUT_DIR MODEL_PATH SCALE NOISE_LEVEL GPU_ARG TILE_SIZE" >&2
    exit 1
fi

mkdir -p "$FRAMES_OUT_DIR"

echo "Upscaling frames (this may take a while)..."
# Note: waifu2x-ncnn-vulkan uses -m for model path, -n for noise (default 0), -s for scale
if [ -z "$NOISE_LEVEL" ]; then
    NOISE_LEVEL="0"
fi
CMD="$WAIFU2X_BIN -i $FRAMES_IN_DIR -o $FRAMES_OUT_DIR -m $MODEL_PATH -s $SCALE -n $NOISE_LEVEL -f png"

if [ -n "$GPU_ARG" ]; then
    CMD="$CMD $GPU_ARG"
fi

if [ -n "$TILE_SIZE" ] && [ "$TILE_SIZE" -gt 0 ]; then
    CMD="$CMD -t $TILE_SIZE"
fi

echo "Running: $CMD"
$CMD
echo "Done."

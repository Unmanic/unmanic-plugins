# Video Upscaler (Dandere2x / Real-ESRGAN / Waifu2x)

Plugin for [Unmanic](https://github.com/Unmanic)

Unmanic plugin that upscales videos using Vulkan-accelerated tools. It extracts frames, upscales them, and re-encodes
video while preserving audio and subtitle streams.

---

### Information:

- [Description](description.md)
- [Changelog](changelog.md)

## What it does

- Upscales video frames with one of three engines:
  - Real-ESRGAN (general-purpose restoration)
  - Waifu2x (anime/line-art friendly)
  - Dandere2x (waifu2x-style video pipeline)
- Skips files that already meet or exceed the target resolution.
- Copies original audio and subtitle streams into the output.

## Choosing the right engine

- Live action / movies / TV: start with Real-ESRGAN.
- Anime / animation: start with Waifu2x (or Real-ESRGAN anime model).
- Need speed on anime-style content: try Dandere2x.

Tip for SD -> 1080p: often faster (and similar quality) to do 2x AI upscaling and finish to 1080p with ffmpeg scaling,
instead of running 4x AI on every frame.

## Requirements

- A GPU with Vulkan support.
- `realesrgan-ncnn-vulkan` and `waifu2x-ncnn-vulkan` binaries.
- Dandere2x dependencies and a venv (installed by the plugin on container restart when running in the Unmanic Docker image).

## Configuration

- Upscaler Tool: Choose the engine (Real-ESRGAN, Waifu2x, or Dandere2x).
- Real-ESRGAN Model: Select general or anime-tuned models.
- Waifu2x Model: Select from installed waifu2x models (for example, `models-cunet`).
- Waifu2x Noise Level: Denoise level passed to waifu2x (`-1` disables denoise, `0-3` increase strength).
- Dandere2x Block Size: Block size used when matching tiles between frames.
- Dandere2x Image Quality: Output image quality setting (default 85).
- Dandere2x Scale Factor: Scale factor (0 omits the flag, default 2).
- Dandere2x Noise Level: Denoise level (0 omits the flag, default 3).
- Dandere2x Processing Type: Select "single" or "multi" processing mode.
- GPU ID: Select which Vulkan GPU to use. `auto` chooses the default device.
  - In Docker: Intel/AMD use `/dev/dri`, NVIDIA uses the NVIDIA runtime.
- Tile Size: Use 0 for auto. Smaller tiles reduce VRAM usage but can slow processing.
- Target Height (Output Resolution): Final output height in pixels (e.g., 1080 or 2160).
  Files already at or above this height are skipped. The plugin warns if the target is more
  than two common steps above the source.
- Ignore files whose height is close to the selected target height: Skip files within 20% of target height.
- FFmpeg Video Encoder Args: FFmpeg arguments for the final encode (for example,
  `-c:v libx264 -crf 20 -preset fast`). Audio and subtitles are copied from the source.

## Performance notes

Upscaling is slow and heavily GPU-dependent. The same file can vary from minutes to hours across GPUs. SD -> 1080p means
lots of frames to process and a large scale factor, so expect long runtimes.

Example ballparks for SD (480p) to 1080p:

- Entry-level iGPU (Intel Iris Xe / similar): 10s of seconds per frame in worst cases, so multi-hour videos can take days.
- Mid-range GPU (RTX 3060 / similar): a few frames per second depending on model/tiling, so a 20 min episode can take hours.
- High-end GPU (RTX 4090 / similar): can reach real-time or better on light models, but heavy models still take significant time.

## References

- Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN
- waifu2x-ncnn-vulkan: https://github.com/nihui/waifu2x-ncnn-vulkan
- Dandere2x: https://github.com/akai-katto/dandere2x
- Performance benchmark: https://openbenchmarking.org/performance/test/pts/realsr-ncnn/0500814264f224aa55132a774d49e3f77c781f13

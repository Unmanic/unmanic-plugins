---

This plugin upscales videos using Vulkan-accelerated tools:

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- [waifu2x-ncnn-vulkan](https://github.com/nihui/waifu2x-ncnn-vulkan)
- [Dandere2x](https://github.com/akai-katto/dandere2x)

It extracts frames, upscales them, then re-encodes the video while preserving audio and subtitle streams.

What each tool is best at:

- **Real-ESRGAN**: General-purpose restoration. Usually better on live action, noisy sources, and mixed content.
  Can add "GAN texture" or artificial detail if pushed too hard.
- **Waifu2x**: Anime/illustration and line-art friendly. Often cleaner on flat shading or UI-heavy content.
  Can oversmooth live action and lose fine natural detail.
- **Dandere2x**: A video pipeline that reuses blocks between frames to speed up waifu2x-style upscaling.
  Best on anime or low-motion footage. Less benefit on heavy motion or grainy sources.

Practical pick:

- Live action / movies / TV: start with Real-ESRGAN.
- Anime / animation: start with Waifu2x (or the Real-ESRGAN anime model).
- Need speed on anime-style content: try Dandere2x.

Tip for SD -> 1080p: often faster (and similar quality) to do 2x AI upscaling and finish to 1080p with ffmpeg scaling,
instead of running 4x AI on every frame.

Features:

- **GPU Acceleration**: Supports Intel, AMD, and NVIDIA GPUs using Vulkan.
- **Tool Choice**: Pick Real-ESRGAN (general purpose), Waifu2x (anime/line-art), or Dandere2x (video-optimized pipeline).
- **Smart Logic**: Skips files that already meet or exceed the target resolution.
- **Seamless Integration**: Maps all original audio and subtitle streams to the upscaled output.

Configuration details:

- **Upscaler Tool**: Choose the upscaling engine. This sets which models and options are visible.
- **Real-ESRGAN Model**: General or anime-tuned models. General models aim for detail recovery on real footage.
- **Waifu2x Model**: Select from installed waifu2x models (for example, `models-cunet`).
- **Waifu2x Noise Level**: Denoise level passed to waifu2x (-1 disables denoise, 0-3 increase strength).
- **Dandere2x Block Size**: Block size used by Dandere2x when matching tiles between frames.
- **Dandere2x Image Quality**: Output image quality setting (default 85).
- **Dandere2x Scale Factor**: Dandere2x scale factor (0 omits the flag, default 2).
- **Dandere2x Noise Level**: Dandere2x denoise level (0 omits the flag, default 3).
- **Dandere2x Processing Type**: Select "single" or "multi" processing mode.
- **GPU ID**: Select which Vulkan GPU to use. `auto` chooses the default device. In Docker:
  Intel/AMD use `/dev/dri`, NVIDIA uses the NVIDIA runtime.
- **Tile Size**: Use 0 for auto. Smaller tiles reduce VRAM usage but can slow processing.
- **Target Height (Output Resolution)**: Final output height in pixels (e.g., 1080 or 2160). Files already at or above
  this height are skipped. The plugin warns if the target is more than two common steps above the source.
- **Ignore files whose height is close to the selected target height**: When enabled, files within 20% of the target
  height are skipped.
- **FFmpeg Video Encoder Args**: FFmpeg arguments for the final encode (for example,
  `-c:v libx264 -crf 20 -preset fast`). Audio and subtitles are copied from the source.

Performance expectations (very rough):

- Upscaling is slow and heavily GPU-dependent. The same file can vary from minutes to hours across GPUs.
- SD -> 1080p means lots of frames to process and a large scale factor, so expect long runtimes.

Example ballparks for SD (480p) to 1080p:

- **Entry-level iGPU** (Intel Iris Xe / similar): 10s of seconds per frame in worst cases, so multi-hour videos can take days.
- **Mid-range GPU** (RTX 3060 / similar): a few frames per second depending on model/tiling, so a 20 min episode can take hours.
- **High-end GPU** (RTX 4090 / similar): can reach real-time or better on light models, but heavy models still take significant time.

For broader performance comparisons, see:
[openbenchmarking](https://openbenchmarking.org/performance/test/pts/realsr-ncnn/0500814264f224aa55132a774d49e3f77c781f13)

Requirements:

- A GPU with Vulkan support.
- `realesrgan-ncnn-vulkan` and `waifu2x-ncnn-vulkan` binaries (downloaded by the plugin on container restart when running in the Unmanic Docker image).
- Dandere2x dependencies and venv (installed by the plugin on container restart when running in the Unmanic Docker image).

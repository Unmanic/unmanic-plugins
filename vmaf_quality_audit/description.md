---

Audit video quality after a worker pipeline has already produced a cached output file by comparing that cached file against the original source with FFmpeg's `libvmaf` filter.

This plugin is designed to sit very late in the worker flow so it can inspect the final cached worker output before post-processing copies files back into the library. During the worker stage it:

- probes the original source and current cached output with `ffprobe`
- runs a VMAF comparison with a configurable FFmpeg binary
- stores source/output video diagnostics
- captures sampled frame-level VMAF scores for frontend graphing

After post-processing completes it persists the audit record together with the final task outcome, destination files, and file movement success state. That means the data panel can show not just the quality score, but whether the overall task ultimately completed, failed during processing, or failed during file movement.

Recommended setup:

- enable the plugin on the target library
- leave it near the end of the worker process flow
- keep it after any transcoding/remuxing worker plugins whose output you want to score

By default the plugin targets the bundled BtbN FFmpeg build at `/usr/lib/btbn-ffmpeg/bin/ffmpeg`, which is expected to include `libvmaf`.

:::important
**Add this plugin last in the Worker - Processing file flow**

This plugin should be placed at the end of the library's **Worker - Processing file** plugin chain.
It audits the final cached worker output, so any transcoding, remuxing, filtering, or other worker-stage changes you want measured should run before this plugin.
:::

---

##### Configuration:

- **FFmpeg Path**
  Path to the FFmpeg binary that will run the `libvmaf` comparison.
  Default: `/usr/lib/btbn-ffmpeg/bin/ffmpeg`
  Recommended: leave on the bundled BtbN FFmpeg path unless you have another FFmpeg build with `libvmaf`.
- **FFprobe Path**
  Path to the FFprobe binary used to inspect the source and audited output files.
  Default: `/usr/lib/btbn-ffmpeg/bin/ffprobe`
  Recommended: leave on the bundled BtbN FFprobe path unless you are using a matching custom FFmpeg toolchain.
- **VMAF Threads**
  Number of threads FFmpeg/libvmaf may use while scoring.
  Set this to `0` to leave thread selection on automatic.
  Default: `0`
  Recommended: `0`
- **Frame Subsample**
  Controls how many frames are scored.
  `1` means every frame is analyzed.
  `2` means every second frame is analyzed.
  Higher values reduce runtime and CPU load, but the result is less precise.
  Default: `1`
  Recommended: `1` for accurate audits, or `2` if you want a modest speedup with some loss of precision.
- **Max Chart Points**
  Limits how many frame score points are stored for the data panel graph.
  This does not change the VMAF calculation itself. It only reduces how much chart data is saved.
  Default: `800`
  Recommended: `800`
- **Fail Task On Analysis Error**
  If enabled, a failed VMAF run will fail the task.
  If disabled, the task result is still recorded and the audit will be marked as missing or failed.
  Default: `Disabled`
  Recommended: `Disabled` while evaluating pipelines, or `Enabled` only if a missing VMAF result should make the task fail.

:::note
**Full-pass analysis**

By default this plugin performs a full VMAF pass across the compared video rather than a quick spot-check.
The main performance control is **Frame Subsample**.
Use a higher subsample value if you want faster audits with lower precision.
:::

:::important
**FFmpeg requirement**

The configured FFmpeg binary must include the `libvmaf` filter.
The bundled Jellyfin FFmpeg build does not include `libvmaf`, which is why this plugin defaults to the bundled BtbN FFmpeg path.
:::

**<span style="color:#56adda">0.0.5</span>**
- Remove enabled config option

**<span style="color:#56adda">0.0.4</span>**
- Record and display VMAF runner timing instead of overall task timing

**<span style="color:#56adda">0.0.3</span>**
- Added file sampling controls with a two-option dropdown for whole-file analysis or sampled one-minute chunks
- Added a conditional sample-count slider to control how many one-minute chunks are compared across the timeline
- Automatically falls back to whole-file analysis when the media duration is shorter than 5 minutes

**<span style="color:#56adda">0.0.2</span>**
- Skip VMAF audits when `original_file_path` and `file_in` resolve to the same file, log a clear configuration warning, and avoid persisting empty audit records

**<span style="color:#56adda">0.0.1</span>**
- Initial release
- Runs a late-stage VMAF audit against the original source and the final cached worker output
- Streams FFmpeg VMAF progress into the worker log and worker progress gauge
- Stores audit history with task result state, destination files, source/output diagnostics, and test duration
- Provides a frontend data panel for reviewing audit history and per-frame VMAF trends

**<span style="color:#56adda">0.0.1</span>**
- Initial release
- Runs a late-stage VMAF audit against the original source and the final cached worker output
- Streams FFmpeg VMAF progress into the worker log and worker progress gauge
- Stores audit history with task result state, destination files, source/output diagnostics, and test duration
- Provides a frontend data panel for reviewing audit history and per-frame VMAF trends

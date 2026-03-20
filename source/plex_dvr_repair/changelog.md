**<span style="color:#56adda">0.0.4</span>**
- Improve scan-time skip logging with explicit reasons for unsupported Plex DVR filename patterns and unsupported source extensions
- Remove the extra debug logging wrapper in the repair logic and log directly through the plugin logger
- Keep the worker-only repair diagnostics reporting added in the previous release

**<span style="color:#56adda">0.0.3</span>**
- Add final repair diagnostics reporting with input fragment summary, ffmpeg findings, and output probe summary
- Categorize ffmpeg warnings encountered during repair so logs show corruption, decode, timestamp, and muxing issues that were worked around

**<span style="color:#56adda">0.0.2</span>**
- Fix MKV outputs to be written as normal finished Matroska files instead of live-style MKV streams
- Remove live/cluster muxing flags that interfered with duration and seekability in Plex playback
- Keep timestamp normalization focused on repair and playback stability with `-avoid_negative_ts make_zero`

**<span style="color:#56adda">0.0.1</span>**
- Initial version
- Adds Plex DVR copy-fragment detection, grouping, repair stitching, chapter preservation, and cleanup controls

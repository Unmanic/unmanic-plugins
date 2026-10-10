
**<span style="color:#56adda">0.0.6</span>**
- add check in calculate_bitrate and custom_stream_mapping to set channels to 6 if channels > 6.  ffmpeg cannot encode > 6 channels of aac audio.

**<span style="color:#56adda">0.0.6</span>**
- add 'ac' parameter to ffmpeg command to ensure proper channel_layout field for compatiability with normalization plugin to avoid unsupported channel layout error

**<span style="color:#56adda">0.0.5</span>**
- Update FFmpeg helper
- Remove support for v1 plugin executor
- Improve audio bitrate calculator to default to x2 channels when calculating if the stream does not define the number of channels
- Fix bug where "Write your own FFmpeg params" options were not being applied correctly to the FFmpeg command

**<span style="color:#56adda">0.0.4</span>**
- Update FFmpeg helper
- Add platform declaration

**<span style="color:#56adda">0.0.3</span>**
- Enabled support for v2 plugin executor

**<span style="color:#56adda">0.0.2</span>**
- Ensure no static vars are used with when stream mapping

**<span style="color:#56adda">0.0.1</span>**
- initial version

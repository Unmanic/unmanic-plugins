
**<span style="color:#56adda">0.0.5</span>**
- Add smart audio filters for maximum channel count and loudness normalization, and warn when a selected codec such as MP3 is a poor fit for multichannel output
- Add new encoder libraries for FLAC, Opus, AC3, and EAC3
- Make the maximum channel-count selector codec-aware so unsupported channel layouts are clamped to the selected codec's supported limit
- Refresh the plugin description and metadata to document the current settings surface and codec channel support warnings
- Add a minimum input channel-count processing threshold so derived stereo streams can be skipped while surround streams continue to be processed
- Add support for generic Unmanic stream ignore markers and document the coordination convention for other plugin authors in the README

**<span style="color:#56adda">0.0.4</span>**
- Rebrand the plugin as Transcode Audio and add support for transcoding audio streams in video/media files while copying non-audio streams and preserving the source container

**<span style="color:#56adda">0.0.3</span>**
- Add smart output target to Basic mode so matching audio codecs can be re-encoded when they are significantly above the recommended bitrate window

**<span style="color:#56adda">0.0.2</span>**
- Update runner signatures to accept keyword helper args for Unmanic compatibility

**<span style="color:#56adda">0.0.1</span>**
- Initial version

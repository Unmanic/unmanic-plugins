
**<span style="color:#56adda">0.0.9</span>**
- fix in 0.0.8 had a bug where the original_sample_rate calculation was in the middle of the return values (moved it just above return stanza)

**<span style="color:#56adda">0.0.8</span>**
- Fixed a bug where the plugin would fail if the max peak was set to 0
- Fixed bug where sample rates would be set to 96kHz

**<span style="color:#56adda">0.0.7</span>**
- add 'ac' parameter to ffmpeg command performing normalization to avoid unsupported channel layout error

**<span style="color:#56adda">0.0.6</span>**
- Update FFmpeg helper
- Add platform declaration

**<span style="color:#56adda">0.0.5</span>**
- Update Plugin for Unmanic v2 PluginHandler compatibility

**<span style="color:#56adda">0.0.4</span>**
- Limit plugin to only process files with a "video" mimetype
- Remove support for older versions of Unmanic (requires >= 0.1.0)
- Fix bug causing already normalised files to be added again (even if they were not reprocessed)

**<span style="color:#56adda">0.0.3</span>**
- Update Plugin for Unmanic v1 PluginHandler compatibility
- Update icon

**<span style="color:#56adda">0.0.2</span>**
- Change to using Unmanic's info files for storing normalise config for a particular file

**<span style="color:#56adda">0.0.1</span>**
- Initial version

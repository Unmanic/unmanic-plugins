
**<span style="color:#56adda">0.0.4</span>**
- Fix TypeError crash when mimetypes.guess_type() returns None (unknown extensions, or a thread race against another plugin's mimetypes.init() during concurrent library scans)
- Fix known-video-extension fallback never matching (os.path.splitext() returns extensions with a leading dot)

**<span style="color:#56adda">0.0.3</span>**
- add option to read duration from format section of ffprobe output

**<span style="color:#56adda">0.0.2</span>**
- Skip checking non-video files

**<span style="color:#56adda">0.0.1</span>**
- Initial version

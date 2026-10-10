
**<span style="color:#56adda">0.0.13</span>**
- add flag to extract untagged subtitle streams
- fix bug that causes only the latest stream to survive when multiple streams have the same tag

**<span style="color:#56adda">0.0.12</span>**
- add back in file test check for presence of text subtitles
- change text of what is written in .unmanic file to prevent against empty string in cases where remove all subtitles is run in same library

**<span style="color:#56adda">0.0.11</span>**
- remove note in description.md about plugin not having a file test section - a file test section was added in v0.0.8

**<span style="color:#56adda">0.0.10</span>**
- Added user of .unmanic file to track processed files

**<span style="color:#56adda">0.0.9</span>**
- Add settings to specify:
  - Which languages to extract
  - Whether to include "title" in output file name 

**<span style="color:#56adda">0.0.8</span>**
- Add library tester to search for files with SRT streams
- Update FFmpeg helper

**<span style="color:#56adda">0.0.7</span>**
- Update FFmpeg helper
- Add platform declaration

**<span style="color:#56adda">0.0.6</span>**
- Update Plugin for Unmanic v2 PluginHandler compatibility

**<span style="color:#56adda">0.0.5</span>**
- Fix bug in stream mapping causing subtitles from the previous file being added to the command of the current file

**<span style="color:#56adda">0.0.4</span>**
- Limit plugin to only process files with a "video" mimetype
- Remove support for older versions of Unmanic (requires >= 0.1.0)
- Fix issue when creating SRT file naming (TypeError: expected string or bytes-like object)
- Add better debug logging

**<span style="color:#56adda">0.0.3</span>**
- Fix import issue in plugin file

**<span style="color:#56adda">0.0.2</span>**
- Update Plugin for Unmanic v1 PluginHandler compatibility
- Update icon

**<span style="color:#56adda">0.0.1</span>**
- Initial version

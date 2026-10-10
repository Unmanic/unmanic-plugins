
**<span style="color:#56adda">0.0.11</span>**
- make init.d installer compatible with new ubuntu 24 unmanic container

**<span style="color:#56adda">0.0.10</span>**
- changed init.d to install the plugin by building from github - installs the latest version with ffmpeg compatibility fixes
- expands use_hw option to be used for either nvidia or intel QSV GPUs
- auto detects GPU
- falls back to CPU based decode if use_hw is selected and plugin determines no GPU or no useable GPU was found

**<span style="color:#56adda">0.0.9</span>**
- add mimetype override and comskip command line arg to support ts files
- add parse_progress to display estimated time of completion

**<span style="color:#56adda">0.0.8</span>**
- fix comcut_path in build_comcut_args - was wrong due to copy/paste error

**<span style="color:#56adda">0.0.7</span>**
- Added h/w accelerated comskip option using cuvid

**<span style="color:#56adda">0.0.6</span>**
- Enabled support for v2 plugin executor

**<span style="color:#56adda">0.0.5</span>**
- Fix issue with check on whether the file has already been processed

**<span style="color:#56adda">0.0.4</span>**
- Match file extension against the source file, not the current cached file.

**<span style="color:#56adda">0.0.3</span>**
- Ensure comchap and comcut scripts are executable
- Add option to limit files based on extension

**<span style="color:#56adda">0.0.2</span>**
- Add comchap and comcut to plugin

**<span style="color:#56adda">0.0.1</span>**
- Initial version

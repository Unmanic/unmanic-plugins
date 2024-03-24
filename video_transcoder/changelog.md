
**<span style="color:#56adda">0.1.4</span>**
- add missing 'generic_kwargs' from return statement in nvenc.py basic config section

**<span style="color:#56adda">0.1.3</span>**
- fix nvenc 10 bit profile name

**<span style="color:#56adda">0.1.2</span>**
- Fix for plugin updates from versions older than 0.1.0

**<span style="color:#56adda">0.1.1</span>**
- Add support for the av1_qsv encoder

**<span style="color:#56adda">0.1.0</span>**
- Stable release
- Prefix QSV config options in plugin settings file to isolate them from libx encoder settings (users will need to reconfigure some QSV settings)
- Prefix VAAPI config options in plugin settings file to isolate them from libx encoder settings (users will need to reconfigure some VAAPI settings)

**<span style="color:#56adda">0.0.10</span>**
- Add support for QSV HW accelerated decoding
- Add support for the scale_qsv filter when using qsv encoding
- Add support for the scale_cuda filter when using nvenc

**<span style="color:#56adda">0.0.9</span>**
- Add support for the h264_vaapi encoder
- Add support for the h264_nvenc encoder
- Add support for the hevc_nvenc encoder

**<span style="color:#56adda">0.0.8</span>**
- update ffmpeg helper library to latest version

**<span style="color:#56adda">0.0.7</span>**
- Handle circumstance where file probe has no 'codec_name'
- Improve library scan speed when used with other plugins that use ffprobe

**<span style="color:#56adda">0.0.6</span>**
- Fix an error in ffmpeg command generator

**<span style="color:#56adda">0.0.5</span>**
- Improvements to ffmpeg command generator
- Fix issue where input file was added before additional main options

**<span style="color:#56adda">0.0.4</span>**
- Add ability to specify a codec in plain text in advanced mode

**<span style="color:#56adda">0.0.3</span>**
- Fix bug where videos would forever be re-added to the task list if force transcoding was enabled

**<span style="color:#56adda">0.0.2</span>**
- Fix detection if video stream is already in the correct codec
- Add ability to strip data and attachment streams from video files

**<span style="color:#56adda">0.0.1</span>**
- Add an "Advanced" configuration option to the plugin's settings
- Add ability to force transcoding of a video when it is already in the desired video codec

**<span style="color:#56adda">0.0.1-beta2</span>**
- Add support for specifying the VAAPI device
- Improvements to code that generates the encoder specific arguments

**<span style="color:#56adda">0.0.1-beta1</span>**
- Initial version


---

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.video_transcoder/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.video_transcoder/pulls)

---

##### Documentation:

For information on the available encoder settings:
- LibX (CPU encoders)
  - [FFmpeg - H.264](https://trac.ffmpeg.org/wiki/Encode/H.264)
  - [FFmpeg - H.265](https://trac.ffmpeg.org/wiki/Encode/H.265)
- QuickSync
  - [FFmpeg - QuickSync](https://trac.ffmpeg.org/wiki/Hardware/QuickSync)
  - [INTEL CPU compatibility chart](https://en.wikipedia.org/wiki/Intel_Quick_Sync_Video#Hardware_decoding_and_encoding).
- VAAPI
  - [FFmpeg - VAAPI](https://trac.ffmpeg.org/wiki/Hardware/VAAPI)
  - [FFmpeg - HWAccelIntro](https://trac.ffmpeg.org/wiki/HWAccelIntro#VAAPI)

---

##### Additional Information:

:::note
**Advanced**

If you set the Config mode to *"Advanced"*, the input text privdes the ability to add FFmpeg commandline args in three different places:
1. **MAIN OPTIONS** - After the default generic options.
   ([Main Options Docs](https://ffmpeg.org/ffmpeg.html#Main-options))
1. **ADVANCED OPTIONS** - After the input file has been specified.
   ([Advanced Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-options))
1. **VIDEO OPTIONS** - After the video is mapped. Here you can specify the video encoder, its params and any additional video options.
   ([Video Options Docs](https://ffmpeg.org/ffmpeg.html#Video-Options))
   ([Advanced Video Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-Video-options))

```
ffmpeg \
    -hide_banner \
    -loglevel info \
    <CUSTOM MAIN OPTIONS HERE> \
    -i /path/to/input/video.mkv \
    <CUSTOM ADVANCED OPTIONS HERE> \
    -map 0:0 -map 0:1 \
    -c:v:0 <CUSTOM VIDEO OPTIONS HERE> \
    -c:a:0 copy \
    -y /path/to/output/video.mkv 
```
:::

:::note
**Force transcoding**

Enabling the *"Force transcoding ..."* option under *"Standard"* mode will force a transcode of the video stream even if it matches the selected video codec.

A file will only be forced to be transcoded once. It will then be flagged in a local `.unmanic` file to prevent it being added to the pending tasks list in a loop.

However, a file previously flagged to be ignored by this will still be transcoded to apply any matching smart filters such as scaling, stripping data streams, etc.
:::

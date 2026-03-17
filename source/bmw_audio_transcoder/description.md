
---

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.audio_transcoder/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.audio_transcoder/pulls)

---

##### Documentation:

For information on the available encoder settings:
- MP3 encoders
  - [FFmpeg - MP3](https://trac.ffmpeg.org/wiki/Encode/MP3)
- AAC
  - [FFmpeg - AAC](https://trac.ffmpeg.org/wiki/Encode/AAC)

---

##### Additional Information:

:::note
The output file extension will always be determined by the selected audio encoder. 
For example, selecting an MP3 encoder will always produce a *XXXX.mp3* file, and selecting an AAC encoder will always produce a *XXXX.m4a* file.
:::

:::note
**Advanced**

If you set the Config mode to *"Advanced"*, the input text provides the ability to add FFmpeg commandline args in three different places:
1. **MAIN OPTIONS** - After the default generic options.
   ([Main Options Docs](https://ffmpeg.org/ffmpeg.html#Main-options))
1. **ADVANCED OPTIONS** - After the input file has been specified.
   ([Advanced Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-options))
1. **AUDIO OPTIONS** - After the audio is mapped. Here you can specify the audio encoder, its params and any additional audio options.
   ([Audio Options Docs](https://ffmpeg.org/ffmpeg.html#Audio-Options))
   ([Advanced Audio Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-Audio-options))

```
ffmpeg \
    -hide_banner \
    -loglevel info \
    <CUSTOM MAIN OPTIONS HERE> \
    -i /path/to/input/audio.wav \
    <CUSTOM ADVANCED OPTIONS HERE> \
    -map 0:0 -c:a:0 <CUSTOM AUDIO OPTIONS HERE> \
    -y /path/to/output/audio.mp3 
```
:::

:::note
**Force transcoding**

Enabling the *"Force transcoding ..."* option will force a transcode of the audio stream even if it matches the selected audio codec.

A file will only be forced to be transcoded once. It will then be flagged in a local `.unmanic` file to prevent it being added to the pending tasks list in a loop.

However, a file previously flagged to be ignored by this will still be transcoded to apply any matching smart filters such as scaling, stripping data streams, etc.
:::

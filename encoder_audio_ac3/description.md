
---

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.encoder_audio_ac3/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.encoder_audio_ac3/pulls)

---

##### Description:

This Plugin will automatically manage bitrate for you. 

- If the stream has 2 or less channels, the bitrate will be set to 224k
- If the stream has 4 or less channels, the bitrate will be set to 448k
- If the stream has more than 4 channels, the bitrate will be set to 640k (max value for encoder)

---

##### Documentation:

- [FFmpeg - High Quality Audio Recommended Bitrates](https://trac.ffmpeg.org/wiki/Encode/HighQualityAudio#Recommendedminimumbitratestouse)

---

### Config description:

#### <span style="color:blue">Max input stream packet buffer</span>
When transcoding audio and/or video streams, ffmpeg will not begin writing into the output until it has one packet for each such stream. 
While waiting for that to happen, packets for other streams are buffered. 
This option sets the size of this buffer, in packets, for the matching output stream.

FFmpeg docs refer to this value as '-max_muxing_queue_size'


#### <span style="color:blue">Write your own FFmpeg params</span>
This free text input allows you to write any FFmpeg params that you want. 
This is for more advanced use cases where you need finer control over the file transcode.

:::note
These params are added in three different places:
1. **MAIN OPTIONS** - After the default generic options.
   ([Main Options Docs](https://ffmpeg.org/ffmpeg.html#Main-options))
1. **ADVANCED OPTIONS** - After the input file has been specified.
   ([Advanced Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-options))
1. **AUDIO OPTIONS** - After the audio stream is mapped and the encoder is selected.
   ([Audio Options Docs](https://ffmpeg.org/ffmpeg.html#Audio-Options))
   ([Advanced Audio Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-Audio-options))

```
ffmpeg \
    -hide_banner \
    -loglevel info \
    <CUSTOM MAIN OPTIONS HERE> \
    -i /path/to/input/video.mkv \
    <CUSTOM ADVANCED OPTIONS HERE> \
    -map 0:0 -map 0:1 \
    -c:v:0 copy \
    -c:a:0 ac3 \
    <CUSTOM AUDIO OPTIONS HERE> \
    -y /path/to/output/video.mkv 
```
:::


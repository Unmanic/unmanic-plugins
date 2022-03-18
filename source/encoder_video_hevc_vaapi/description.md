For information on the hevc_vaapi encoder settings:

- [FFmpeg - VAAPI](https://trac.ffmpeg.org/wiki/Hardware/VAAPI)
- [FFmpeg - HWAccelIntro](https://trac.ffmpeg.org/wiki/HWAccelIntro#VAAPI)

Check your GPU compatibility:

- [INTEL CPU compatibility chart](https://en.wikipedia.org/wiki/Intel_Quick_Sync_Video#Hardware_decoding_and_encoding).

### Config description:

#### <span style="color:blue">Enable VAAPI HW Accelerated Decoding?</span>
Decode the video stream using hardware accelerated decoding. 
This enables full hardware transcode with VAAPI, using only hardware acceleration entire video transcode.

When the input may or may not be hardware decodable, this will fallback to software decoding.

#### <span style="color:blue">Max input stream packet buffer</span>
When transcoding audio and/or video streams, ffmpeg will not begin writing into the output until it has one packet for each such stream. 
While waiting for that to happen, packets for other streams are buffered. 
This option sets the size of this buffer, in packets, for the matching output stream.

FFmpeg docs refer to this value as '-max_muxing_queue_size'


#### <span style="color:blue">Overwrite all options with custom input</span>
This free text input allows you to write any FFmpeg params that you want. 
This is for more advanced use cases where you need finer control over the file transcode.

:::note
These params are added in three different places:
1. **MAIN OPTIONS** - After the default generic options.
   ([Main Options Docs](https://ffmpeg.org/ffmpeg.html#Main-options))
1. **ADVANCED OPTIONS** - After the input file has been specified.
   ([Advanced Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-options))
1. **VIDEO OPTIONS** - After the video is mapped and the encoder is selected.
   ([Video Options Docs](https://ffmpeg.org/ffmpeg.html#Video-Options))
   ([Advanced Video Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-Video-options))

```
ffmpeg \
    -hide_banner \
    -loglevel info \
    <CUSTOM MAIN OPTIONS HERE> \
    -i /library/TEST_FILE.mkv \
    <CUSTOM ADVANCED OPTIONS HERE> \
    -map 0:v:0 \
    -map 0:a:0 \
    -map 0:a:1 \
    -c:v:0 hevc_vaapi \
    <CUSTOM VIDEO OPTIONS HERE> \
    -c:a:0 copy \
    -c:a:1 copy \
    -y /path/to/output/video.mkv 
```
:::

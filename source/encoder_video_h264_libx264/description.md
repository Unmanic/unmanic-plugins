
For information on the libx264 encoder settings:
[FFmpeg - H.264](https://trac.ffmpeg.org/wiki/Encode/H.264)


### Config description:


#### <span style="color:blue">Constant Rate Factor (CRF):</span>
The range of the CRF scale is 0–51, where 0 is lossless, 23 is the default, and 51 is worst quality possible. 

A lower value generally leads to higher quality, and a subjectively sane range is 17–28. 

Consider 17 or 18 to be visually lossless or nearly so; it should look the same or nearly the same as the input but it isn't technically lossless. 


#### <span style="color:blue">Quality Preset:</span>
A preset is a collection of options that will provide a certain encoding speed to compression ratio. 
A slower preset will provide better compression (compression is quality per filesize). 
This means that, for example, if you target a certain file size or constant bit rate, you will achieve better quality with a slower preset. 
Similarly, for constant quality encoding, you will simply save bitrate by choosing a slower preset. 


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
    -i /path/to/input/video.mkv \
    <CUSTOM ADVANCED OPTIONS HERE> \
    -map 0:0 -map 0:1 \
    -c:v:0 libx264 \
    <CUSTOM VIDEO OPTIONS HERE> \
    -c:a:0 copy \
    -y /path/to/output/video.mkv 
```
:::

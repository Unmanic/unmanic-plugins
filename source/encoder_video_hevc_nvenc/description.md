
For information on the hevc_nvenc encoder settings:
 - [NVIDIA FFmpeg Transcoding Guide](https://developer.nvidia.com/blog/nvidia-ffmpeg-transcoding-guide/)
 - [FFmpeg - HWAccelIntro](https://trac.ffmpeg.org/wiki/HWAccelIntro#NVENC)

Check your GPU compatibility:
 - [GPU compatibility table](https://developer.nvidia.com/video-encode-and-decode-gpu-support-matrix-new).


### Config description:

#### <span style="color:blue">Enable NVDEC HW Accelerated Decoding?</span>
Decode the video stream using hardware accelerated decoding. This enables full hardware transcode with NVDEC and NVENC, using only GPU memory for the entire video transcode.

This value sets '-hwaccel cuda -hwaccel_device {device}' in the ffmpeg main options. 

It is recommended that for 10-bit encodes, disable this option.


#### <span style="color:blue">NVENC Encoder Quality Preset</span>
A preset is a collection of options that will provide a certain encoding speed to compression ratio. 
A slower preset will provide better compression (compression is quality per filesize). 
This means that, for example, if you target a certain file size or constant bit rate, you will achieve better quality with a slower preset. 
Similarly, for constant quality encoding, you will simply save bitrate by choosing a slower preset. 

This plugin will also set FFmpeg to run in a single thread for 'Slow' and 'Lossless' presets to improve quality.


#### <span style="color:blue">Profile</span>
The profile determines which features of the codec are available and enabled, while also affecting other restrictions. 

The Main profile is capable of 8-bit, Main 10-bit is capable of 10-bit, and Range Extended is capable of more than 10-bit. 
Any of these profiles are capable of 4:2:0, 4:2:2 and 4:4:4, however the support depends on the installed hardware.


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
    -c:v:0 hevc_nvenc \
    <CUSTOM VIDEO OPTIONS HERE> \
    -c:a:0 copy \
    -c:a:1 copy \
    -y /path/to/output/video.mkv 
```
:::


[//]: <> (NOTES:)
[//]: <> (https://github-wiki-see.page/m/Xaymar/obs-StreamFX/wiki/Encoder-FFmpeg-NVENC)

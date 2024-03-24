
This plugin will transcode any video files into H265/HEVC Using Intel's Quick Sync Video encoder.

This plugin is able to work fine with the default settings with no configuration required, 
or you can customise complex filters and command-line options to apply them to the FFmpeg command.

For information on the hevc_qsv encoder settings:

- [FFmpeg - QuickSync](https://trac.ffmpeg.org/wiki/Hardware/QuickSync)

Check your GPU compatibility:

- [INTEL CPU compatibility chart](https://en.wikipedia.org/wiki/Intel_Quick_Sync_Video#Hardware_decoding_and_encoding).

---

### Config description:

#### <span style="color:blue">Max input stream packet buffer</span>
When transcoding audio and/or video streams, ffmpeg will not begin writing into the output until it has one packet for each such stream. 
While waiting for that to happen, packets for other streams are buffered. 
This option sets the size of this buffer, in packets, for the matching output stream.

FFmpeg docs refer to this value as '-max_muxing_queue_size'


#### <span style="color:blue">Encoder quality preset</span>
Select the quality profile for the QSV encoder to use.
- [Intel Quicksync FFmpeg Whitepaper](https://www.intel.com/content/dam/www/public/us/en/documents/white-papers/cloud-computing-quicksync-video-ffmpeg-white-paper.pdf)
- [FFmpeg Preset](https://trac.ffmpeg.org/wiki/Encode/H.264#Preset)


#### <span style="color:blue">Tune for a particular type of source or situation</span>
Tune the output settings based on the specifics of your input.
- [FFmpeg Tune](https://trac.ffmpeg.org/wiki/Encode/H.264#Tune)


#### <span style="color:blue">Encoder ratecontrol method</span>
Select the encoder ratecontrol method. Some encoder modes are quality-based while others are bitrate-based.


:::note
Not all modes are added to this Plugin.
I have selected the most common in order to simplify the configuration of this Plugin.
:::

:::tip
Set a quality-based control to have FFmpeg attempt to match the quality of the source file at a lower bitrate.
:::

- [FFmpeg QSV encoders](https://www.ffmpeg.org/ffmpeg-codecs.html#QSV-encoders)


#### <span style="color:blue">Constant quantizer/quality scale</span>
Available when configuring the ratecontrol using a quality-based method.

Lower values will produce better quality with 1 being close to the source quality.


#### <span style="color:blue">Bitrate</span>
Available when configuring the ratecontrol using a bitrate-based method.

The target (average) bit rate for the encoder to use. If CBR is selected as the ratecontrol method,
then this target will be made constant rather than just an average.


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
    -c:v:0 hevc_qsv \
    <CUSTOM VIDEO OPTIONS HERE> \
    -c:a:0 copy \
    -c:a:1 copy \
    -y /path/to/output/video.mkv 
```
:::


---

##### Links:

- [Support](https://unmanic.app/discord)

---

##### Description:

This plugin creates an additional stereo audio stream using the native ffmpeg aac encoder or,
if selected, using libfdk_aac (requires ffmpeg 5.x)


This Plugin uses 64k per audio channel, so 128 kbps for stereo. 

---

##### Documentation:

For information on the available encoder settings:
- [FFmpeg - AAC Encoder](https://trac.ffmpeg.org/wiki/Encode/AAC)

--- 

### Config description:

#### <span style="color:blue">Language</span>
Specify language tag to search for in source stream

#### <span style="color:blue">Channels</span>
Specify number of channels to be searched for in source stream

#### <span style="color:blue">Codec Name</span>
Specify which encoding to search for in source stream (by codec name)

#### <span style="color:blue">Encoder Selection</span>
Leave unchecked to select native ffmpeg aac encoder, libfdk_aac requires ffmpeg 5.x

:::note
This plugin will create a stereo aac or libfdk_aac stream as an additional stereo stream.
It will search for the first stream matching the search parameters and encode that as an
additional 2 channel stereo audio using aac or, if selected, libfdk_aac (ffmpeg 5 only).

If any of the search parameters are left blank, this plugin will select the first stream with a
number of audio channels > 4 and encode that as the additional 2 channel stereo stream

For this plugin to work successfully, audio streams must have proper language tags - particularly
the stream that is to be re-encoded as an additional stereo stream
:::


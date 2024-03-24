
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
Specify language tag to search for in source stream - must be specified

#### <span style="color:blue">Channels</span>
Specify number of channels to be searched for in source stream, may be empty

#### <span style="color:blue">Codec Name</span>
Specify which encoding to search for in source stream (by codec name), may be empty

#### <span style="color:blue">Encoder Selection</span>
Leave unchecked to select native ffmpeg aac encoder, libfdk_aac requires ffmpeg 5.x

#### <span style="color:blue">Remove Original Multichannel Audio Stream</span>
Check if you wish to remove the identified/specified multichannel audio stream - otherwise the new stream is added

#### <span style="color:blue">new stereo audio to be the default audio upon playing</span>
Check if you wish to make the new stereo audio be the default audio - if unchecked, default audio is not changed

:::note
This plugin will create a stereo aac or libfdk_aac stream as an additional stereo stream.
It will search for the first stream matching the search parameters and encode that as an
additional 2 channel stereo audio using aac or, if selected, libfdk_aac (ffmpeg 5 only).

If either channels or codec name search parameters are left blank, this plugin will select the first stream with a
number of audio channels > 4 and language matching specified language and encode that as the additional 2 channel stereo stream

For this plugin to work successfully, audio streams must have proper language tags - particularly
the stream that is to be re-encoded as an additional stereo stream

If you opt to remove the original multichannel audio stream, the stereo audio stream will occupy it's
place and all other streams will be left intact

If you wish to only keep a single language, stereo audio stream, the best current method would be to 
use the keep audio stream by language plugin to keep only streams of a specific language, and then
follow that with this plugin and opt to remove the original multichannel audio stream
:::


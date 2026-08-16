---

Audio Transcoder transcodes audio streams in both audio-only files and video/media containers.

For audio-only files, the output extension is determined by the selected encoder.
For video/media files, the plugin preserves the original container and copies all non-audio streams unchanged while transcoding the audio stream or streams.

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.audio_transcoder/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.audio_transcoder/pulls)

---

##### Configuration Modes:

- **Basic**: choose the target codec and encoder, optionally enable smart output target, and optionally enable the plugin's smart audio filters.
- **Standard**: exposes encoder-specific bitrate and rate-control settings, plus optional custom audio filters.
- **Advanced**: write the FFmpeg audio options directly.

---

##### Smart Features:

- **Smart output target** estimates a suitable destination bitrate from the source stream and the selected codec.
- **Re-encode matching codecs above target** is optional and only applies when smart output target is enabled in Basic mode.
- **Only process streams with at least this many channels** can be used to skip lower-channel-count streams such as derived stereo tracks while still processing surround streams in the same file.
- **Enable plugin's smart audio filters** exposes:
  - **Set maximum channel count** to cap the output stream to `7.1`, `5.1`, `2.0`, `1.0`, or keep it the same as the source.
  - **Normalise audio volume levels** to apply FFmpeg loudness normalization.
- The plugin also supports ignoring streams marked with generic Unmanic metadata markers when the container preserves stream metadata reliably.

---

##### Codec Support:

:::warning
Object-based formats such as Dolby Atmos are not preserved by this plugin when transcoding with FFmpeg's open, channel-based encoders.
In practice, the object metadata and immersive rendering information are discarded and the output becomes a conventional channel-based stream such as `7.1`, `5.1`, or `2.0`.
This is largely a limitation of the available FFmpeg/open-source encoder stack and Dolby licensing, not just a plugin choice.
:::

| Codec                     | Practical Max                                 | Good For                                                        | Avoid When                                    | Notes                                                                                                                                                                 |
| ------------------------- | --------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AAC                       | `7.1` technically, `5.1` or below recommended | Stereo music, simple media files, broad client compatibility    | `7.1` home-theater movie audio                | Very widely supported, especially for stereo. `5.1` can work, but `7.1` AAC is a poor fit for movies because channel mapping and playback behavior can be unreliable. |
| FLAC                      | `7.1`                                         | Lossless music, archival use, controlled playback setups        | Maximum device compatibility                  | Best lossless option in this plugin. Great quality, but support across devices and containers is less consistent than AAC or AC3.                                     |
| Opus                      | `7.1`                                         | Efficient compression, modern clients, MKV/WebM libraries       | Older devices and broad compatibility targets | Very efficient and supports high channel counts, but playback support is less consistent than AAC or AC3 in many consumer setups.                                     |
| AC3 (Dolby Digital)       | `5.1`                                         | Movie libraries, AVR compatibility, simple surround playback    | `7.1` source preservation                     | Good fit for home-theater use. FFmpeg's AC3 encoder is limited to `5.1`, so anything above that will be downmixed.                                                    |
| EAC3 (Dolby Digital Plus) | `5.1` in this FFmpeg-based plugin             | Movie libraries, AVR compatibility, efficient surround playback | `7.1` source preservation                     | Similar to AC3 here, but a little more efficient. In this FFmpeg/open-encoder workflow it is effectively capped at `5.1`.                                             |
| MP3                       | `2.0`                                         | Stereo music, simple audio files, legacy client support         | Surround movie audio                          | Treat MP3 as stereo-only here. It is a good fit for basic stereo playback, but multichannel sources will be downmixed.                                                |

:::note
Codec channel limits are enforced by the plugin because they reflect FFmpeg encoder support and practical playback behavior, not arbitrary plugin rules.
When you choose a codec that supports fewer channels than the source, the output will be downmixed to the selected or supported maximum.
:::

---

##### Container Support Breakdown for Codecs:

| Audio Codec | MP4 (`.mp4`) | MKV (`.mkv`) | WebM (`.webm`) | MOV (`.mov`) | AVI (`.avi`) | TS (`.ts`) |
| ----------- | ------------ | ------------ | -------------- | ------------ | ------------ | ---------- |
| AAC         | ✅ Yes       | ✅ Yes       | ❌ No          | ✅ Yes       | ✅ Yes       | ✅ Yes     |
| AC-3 / EAC3 | ✅ Yes       | ✅ Yes       | ❌ No          | ✅ Yes       | ⚠️ Partial   | ✅ Yes     |
| MP3         | ✅ Yes       | ✅ Yes       | ❌ No          | ✅ Yes       | ✅ Yes       | ✅ Yes     |
| Opus        | ⚠️ Hacky     | ✅ Yes       | ✅ Yes         | ❌ No        | ❌ No        | ❌ No      |
| FLAC        | ⚠️ Hacky     | ✅ Yes       | ✅ Yes         | ❌ No        | ❌ No        | ❌ No      |

:::note
This table is a practical compatibility guide for common FFmpeg/container combinations, not a guarantee that every player or device will behave the same way.
Entries marked **Hacky** generally rely on combinations that may mux but are not broadly interoperable.
Entries marked **Partial** may work in some workflows but are less predictable across playback environments.
:::

---

##### Encoder Notes:

- **AAC** is a good general-purpose target for music files and simpler media workflows, but it is not the best choice for high-channel-count home-theater movie audio.
- **FLAC** is the lossless option.
- **Opus** is efficient and supports multichannel output, but some playback environments are less compatible than AAC or AC3.
- **AC3 / EAC3** are useful for home-theater-oriented compatibility, but FFmpeg's available encoders here are capped below `7.1`, so the plugin enforces that same limit.
- **MP3** is best treated as a stereo-oriented target for music and simple audio files.

---

##### Advanced Mode:

If you set the config mode to **Advanced**, the input text provides the ability to add FFmpeg command-line args in three different places:

1. **Main Options**: inserted after the default generic options.
1. **Advanced Options**: inserted after the input file has been specified.
1. **Audio Options**: inserted after the audio stream is mapped. Here you specify the encoder and any additional audio options.

```bash
ffmpeg \
    -hide_banner \
    -loglevel info \
    <CUSTOM MAIN OPTIONS HERE> \
    -i /path/to/input/media.file \
    <CUSTOM ADVANCED OPTIONS HERE> \
    -map 0:a:0 -c:a:0 <CUSTOM AUDIO OPTIONS HERE> \
    -y /path/to/output/media.file
```

---

##### Force Transcoding:

Enabling **Force transcoding even if the file is already using the desired audio codec** will re-encode matching-codec files one time.

The plugin writes a marker so that force-transcoded files are not added back into the pending task list in a loop on subsequent scans.

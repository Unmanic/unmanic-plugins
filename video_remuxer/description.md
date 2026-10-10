
This plugin will remux your files to the configured output video container.

It will attempt to transcode any streams not supported by the configured output container.

If the stream is unable to be transcoded, this plugin will remove that stream.

---

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.video_remuxer/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.video_remuxer/pulls)

---

##### Additional Information:


:::tip
Ensure that your container already supports the streams contained in the source file.
Different containers support different stream codecs.
Especially note subtitle streams. To avoid issues with subtitles, consider also using a Plugin to strip subtitles from the file prior to remuxing.
:::




<div style="background-color:#cfd;border-radius:4px;border-left:solid 5px #2b4;padding:10px;">
<b>Tip:</b>
<br>Ensure that your container already supports the streams contained in the source file.
<br>Different containers support different stream codecs.
<br>Especially note subtitle streams. To avoid issues with subtitles, consider also using a Plugin to strip subtitles from the file prior to remuxing.
</div>

---

#### How this plugin works:

This plugin will remux your files to the configured output video container.

It will attempt to transcode any streams not supported by the configured output container.

If the stream is unable to be transcoded, this plugin will remove that stream.

If you suspect a stream is being incorrectly transcoded or removed during this remux process, 
report it [here](https://github.com/Unmanic/unmanic-plugins/issues) with your FFmpeg log command log.



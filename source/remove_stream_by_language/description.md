
Enter a comma separated list of language codes to search for during library scans and new file event triggers.

Any video files with audio/subtitle streams having tags that match these language codes listed here will be removed from their files.

Three letter language codes might be required because of change to negative stream selection

---

#### Examples:

###### <span style="color:magenta">Remove Japanese and French streams</span>
```
jp,fr
```

#### <span style="color:blue">Write your own FFmpeg params</span>
This free text input allows you to write any FFmpeg params that you want.
This is for more advanced use cases where you need finer control over the file transcode.

:::note
These params are added in three different places:
1. **MAIN OPTIONS** - After the default generic options.
   ([Main Options Docs](https://ffmpeg.org/ffmpeg.html#Main-options))
1. **ADVANCED OPTIONS** - After the input file has been specified.
   ([Advanced Options Docs](https://ffmpeg.org/ffmpeg.html#Advanced-options))

```
ffmpeg \
    -hide_banner \
    -loglevel info \
    <MAIN OPTIONS HERE> \
    -i /path/to/input/video.mkv \
    <ADVANCED OPTIONS HERE> \
    -map 0 \
    -map -0:m:language:jp -map -0:m:language:fr \
    -c copy \
    -y /path/to/output/video.mkv
```
:::

---

#### Custom FFmpeg params Examples:

###### <span style="color:magenta">Set first audio track to default</span>
**<span style="color:blue">Main options</span>**
> *(NONE)*
>
**<span style="color:blue">Advanced options</span>**
> `-disposition:a:0 default`

###### <span style="color:magenta">Remove default flag from all subtitles</span>
**<span style="color:blue">Main options</span>**
> *(NONE)*
>
**<span style="color:blue">Advanced options</span>**
> `-disposition:s 0`

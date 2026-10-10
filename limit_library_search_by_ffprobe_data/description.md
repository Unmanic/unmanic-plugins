
Enter a comma separated list of FFprobe fields to search for during library scans and new file event triggers.

Only files with matching FFprobe field values will be further processed by the file test plugins.

---

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.limit_library_search_by_ffprobe_data/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.limit_library_search_by_ffprobe_data/pulls)

---

##### Documentation:

For information on formulating JSONata queries:
- [JSONata Documentation](https://docs.jsonata.org/overview.html)
- [JSONata Exerciser Tool](https://try.jsonata.org/pdNmg6BId)

---

##### Additional Information:

Try the **JSONata Exerciser Tool** listed in the Documentation above.

###### Examples:

Find all streams matching codec_name field of "h264".

  - **The FFprobe field to match against**
    ```
    $.streams[*].codec_name
    ```
  - **Search strings**
    ```
    h264
    ```

Find all subtitle streams matching codec_name field of "subrip".

  - **The FFprobe field to match against**
    ```
    $.streams[codec_type="subtitle"].codec_name
    ```
  - **Search strings**
    ```
    subrip
    ```

Find all video streams matching codec_name field of "hevc" or "h264" if the video stream is greater than 1000px but smaller than 2000px (1080p).

  - **The FFprobe field to match against**
    ```
    [$.streams[codec_type="video" and (coded_height > 1000) and (coded_height < 2000)].codec_name]
    ```
  - **Search strings**
    ```
    hevc,h264
    ```

Find files with a duration greater than 5 minutes.

  - **The FFprobe field to match against**
    ```
    [$.format.duration > 300 ? "true" : "false"]
    ```
  - **Search strings**
    ```
    true
    ```

:::warning
**Quotes**

The Python library used to parse the JSONata query does not support single quotes. Always use double quotes in your query as in the examples above.
:::


Filter Unmanic's library scan by video dynamic range. Choose whether to allow only HDR or only SDR files, and optionally restrict HDR to specific formats (comma-separated) such as HDR, HDR10, HDR10+, Dolby Vision, or HLG; everything else is skipped before later file test plugins run. Uses ffprobe (bundled) and shares the parsed probe JSON with subsequent plugins via `shared_info`.

---

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.limit_library_search_by_video_dynamic_range/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.limit_library_search_by_video_dynamic_range/pulls)

---

##### Documentation:
- Configure `Allow only HDR or SDR files` in plugin settings.
- When HDR is allowed, enable `Limit to a specific HDR format` to only pass your chosen HDR type (comma-separated list). Supported values: HDR, HDR10, HDR10+, Dolby Vision, HLG.
- If the detected dynamic range does not match, the file is removed from the pending tasks list.
- Parsed ffprobe data is cached in `shared_info["ffprobe"]` so later plugins can reuse it.

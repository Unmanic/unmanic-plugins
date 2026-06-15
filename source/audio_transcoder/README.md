# Transcode Audio

Plugin for [Unmanic](https://github.com/Unmanic)

---

### Information:

- [Description](description.md)
- [Changelog](changelog.md)

---

### Plugin Coordination

`Transcode Audio` can be configured to work alongside other audio-manipulation plugins in two ways:

- **Minimum input channel count**: only process streams at or above a configured source channel-count threshold. This is useful when another plugin creates derived stereo streams and you only want this plugin to continue standardizing surround streams.
- **Unmanic stream ignore markers**: skip streams that have been explicitly marked by another plugin as derived or otherwise not intended for further audio-transcoder processing.

#### Recommended Marker Convention

Where the target container preserves stream metadata reliably, other plugins should write a stream `comment` tag containing semicolon-separated key/value pairs, for example:

```text
unmanic.managed=true;unmanic.source_plugin=add_extra_stereo_audio;unmanic.ignore_for=audio_transcoder
```

`Transcode Audio` currently understands these ignore markers:

- `unmanic.ignore=true`
- `unmanic_ignore=1`
- `unmanic.ignore_for=audio_transcoder`
- `unmanic.ignore_for=all`
- `unmanic_ignore_for=audio_transcoder`
- `unmanic_ignore_for=all`

The plugin reads these markers from:

- explicit stream tags with those names, when the container preserves them
- `comment`
- `description`

#### Notes For Plugin Authors

- This convention is intended for **audio streams inside media containers**, not as a universal guarantee for raw audio-only formats.
- `MKV` is the safest target for preserving these markers.
- `WebM` may preserve them depending on the muxing path and player support.
- `MP4` is more restrictive, so plugins should treat these markers as best-effort there.
- If you generate derivative stereo or commentary/helper streams, prefer marking only the derived stream rather than suppressing the whole file.

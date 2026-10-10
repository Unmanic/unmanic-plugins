---

Repairs interrupted Plex DVR transport stream recordings that were split across a base `.ts` file and one or more sibling ` (copy N)` fragments.

The plugin scans only the base recording, waits for Plex sidecar activity to settle, groups fragments by probed duration plus timestamp progression, and then repairs only the latest logical recording attempt into a single repaired output with `ffprobe`-driven stream selection and `ffmpeg` concat processing.

Key behaviors:

- Ignores individual ` (copy N)` fragments during library scans.
- Detects and skips recordings that still have active Plex sidecars such as `.log`, `.txt`, or `.logo.txt`.
- Splits duplicate recordings into separate logical groups when the fragment timestamps no longer fit the expected recording timeline, then keeps only the latest group.
- Repairs timestamp issues with a stable remux/transcode path instead of unsafe binary concatenation.
- Preserves chapter markers by merging source chapter metadata when comskip/comchap chapters are present.
- Supports output profiles for source-matched output, H.264 MKV, and H.265 MKV.
- Preserves source metadata and includes MKV-safe subtitle and attachment streams when the output container is Matroska.
- Always produces one canonical repaired output, replaces the original base recording with that repaired result, and removes the original fragments only after post-processing completes successfully.

Main settings:

- `ignore_recently_modified_minutes`: ignore recordings that have been touched recently, including the main file, copy fragments, and Plex post-processing activity.
- `use_hardware_acceleration`: try hardware encoding before falling back to software.
- `output_profile`: choose between source-matched output, H.264 MKV, or H.265 MKV.

The plugin currently targets Plex DVR fragment sets discovered from `.ts` base recordings.

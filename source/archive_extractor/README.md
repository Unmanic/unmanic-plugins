# Archive Extractor

Archive Extractor adds archive inputs to an Unmanic library workflow.

It is intended to address [Unmanic issue #612](https://github.com/Unmanic/unmanic/issues/612).

## Supported inputs

- ZIP
- RAR
- New-style multipart RAR sets such as `movie.part01.rar`, `movie.part02.rar`
- Old-style RAR sets such as `movie.rar`, `movie.r00`, `movie.r01`

Only the primary archive volume is queued so multipart sets are not processed repeatedly.

## Workflow

1. Unmanic's library scan discovers the archive.
2. Archive Extractor extracts the largest supported video file.
3. The extracted video becomes the input for the remaining worker plugins.
4. After successful processing, the final media file is written beside the source archive using the extracted video's filename.
5. The archive is preserved by default. Optional deletion occurs only after successful processing and successful file movement.

## RAR dependency

ZIP extraction uses Python's standard library and needs no extra package.

RAR extraction requires one of these commands inside the Unmanic runtime/container:

- `7z`
- `7zz`
- `unrar`

If none is available, the worker reports a clear error and keeps the source archive untouched.

## Settings

- **Enable ZIP archives**
- **Enable RAR archives**
- **Delete archive after successful processing**
- **Video extensions**

## Safety

ZIP members are flattened into Unmanic's task cache rather than extracted to archive-provided paths. This avoids ZIP path traversal. Archives are never deleted when worker processing or final file movement fails.

## Current scope

Version 0.1.1 intentionally selects the largest supported video in an archive. Archives containing multiple full-length videos are not split into multiple Unmanic tasks yet.

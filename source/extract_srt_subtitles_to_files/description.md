
Any SRT subtitle streams found in the file will be exported as *.srt files in the same directory as the original file.

:::warning
This plugin is not compatible with linking as the remote link will not have access to the original source file's directory.
:::

To include other formats, such as ASS, consider first converting the subtitle streams to SRT using the Plugin(s) 

Install the **"Convert any ASS subtitle streams in videos to SRT"** plugin and configure the plugin flow to set it before this one

:::note
This Plugin does not contain a file tester to detect files that contain SRT subtitle streams.
Ensure it is pared with another Plugin.
:::

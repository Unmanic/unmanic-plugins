The plugin allows you to run mkvpropedit on a file.

There are some pre-build arguments that you can turn on with a checkbox like:

- Add Track Statistics Tags: This adds `--add-track-statistics-tags` to your arguments
- Remove Title Tag: This adds `-d title` to your arguments
- Add Encode Source To Global Tags: This takes the original file name passed into unmanic, and adds it as a global tag to the mkv file

Anything not built in can be added to the Other Arguments section.

---

#### Important Note

You must make sure that mkvpropedit is installed and available in the PATH so that this plugin can use it. 

If you are running Unmanic with Docker using the official Docker image, this plugin will automatically install the dependencies when you next restrt or recreate the container.

To install mkvpropedit on an Ubnuntu distro you can do something like this:

```sh
#!/bin/bash

apt-get update
apt-get install -y mkvtoolnix
```

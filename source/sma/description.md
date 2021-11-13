

For information on the sickbeard_mp4_automator script settings:

- [SMA script GitHub](https://github.com/mdhiggins/sickbeard_mp4_automator/)
- [AutoProcess Settings](https://github.com/mdhiggins/sickbeard_mp4_automator/wiki/autoProcess-Settings)
- [Manual Script Usage](https://github.com/mdhiggins/sickbeard_mp4_automator/#manual-script-usage)

### Config description:

#### <span style="color:blue">Only run when the original source file matches specified extensions</span>

Enables the option to limit this plugin to only test and run against files matching the configured list of file
extensions.

#### <span style="color:blue">Comma separated list of file extensions</span>

A list of extensions for files that the plugin should test and process. A file with any other extension will be ignored.

#### <span style="color:blue">SMA configuration</span>

Enter your `autoProcess.ini` configuration here. The plugin's default configuration is pretty much the same as the
default hosted in the sickbeard_mp4_automator GitHub repo but with the ffmpeg paths modified for use in Linux.

The following options are overwritten by this plugin and so will not do anything when executed:

- `post-process` - This plugin will disable the execution of additional post processing scripts by the SMA script.
- `delete-original` - As Unmanic processes all files in a cache directory, this config option is irrelevant and so is
  forced to be disabled.
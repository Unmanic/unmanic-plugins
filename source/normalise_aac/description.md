
For information on the normalisation settings:
- [http://johnriselvato.com/ffmpeg-how-to-normalize-audio/](http://johnriselvato.com/ffmpeg-how-to-normalize-audio/)


For more advanced information on the "loudnorm" filter being used:
- [https://ffmpeg.org/ffmpeg-filters.html#loudnorm](https://ffmpeg.org/ffmpeg-filters.html#loudnorm)


### Config description:

#### <span style="color:blue">The integrated loudness target</span>
This can be understood as the "overall" or "average power" level of your audio.
- Range is '**-70.0**' to '**-5.0**'. 
- Default value is '**-24.0**'.

#### <span style="color:blue">Loudness range</span>
Loudness range measures the variation of loudness over your entire track.
- Range is '**1.0**' to '**20.0**'. 
- Default value is '**7.0**'.

#### <span style="color:blue">Maximum true peak</span>
The absolute maximum level of the signal waveform.
- Range is '**-9.0**' to '**+0.0**'. 
- Default value is '**-2.0**'.

#### <span style="color:blue">Ignore all files previously normalised with this plugin</span>
If this is selected, the plugin will ignore any files found that have been tagged by the plugin as having already been normalised.

If this is unselected, then the plugin will only ignore files that are found to have been normalised by this plugin with the exact same settings configured.

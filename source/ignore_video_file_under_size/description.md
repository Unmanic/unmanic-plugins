Specify your minimum file size as Size/Time, eg. <span style="color:DodgerBlue">3.2GB/h</span>.

### Resolution scaling
The plugin will assume your setting is for a <span style="color:DodgerBlue">1080p</span> video and will scale the threshold up or down depending on the actual resolution of your video.


For example, if you put <span style="color:DodgerBlue">1GB/h</span> the plugin will calculate and use the following as the actual threshold:
- <span style="color:DodgerBlue">640*480</span> == <span style="color:DodgerBlue">148.1 MB/hour</span>
- <span style="color:DodgerBlue">1280*720</span> == <span style="color:DodgerBlue">444.4 MB/hour</span>
- <span style="color:DodgerBlue">1920*1080</span> == <span style="color:DodgerBlue">1 GB/hour</span>
- <span style="color:DodgerBlue">3840*2160</span> == <span style="color:DodgerBlue">4 GB/hour</span>

`actual_threshold = your_threshold * (actual_resolution/1080p)`

Note that this is not limited to these specific resolutions, it will scale accurately no matter the size or shape of your video.

### Size format
Sizes can be written as:

- Bytes (Eg. '<span style="color:DodgerBlue">50</span>' or '<span style="color:DodgerBlue">800 B</span>')
- Kilobytes (Eg. '<span style="color:DodgerBlue">100KB</span>' or '<span style="color:DodgerBlue">23 K</span>')
- Megabytes (Eg. '<span style="color:DodgerBlue">9M</span>' or '<span style="color:DodgerBlue">34 MB</span>')
- Gigabytes (Eg. '<span style="color:DodgerBlue">4GB</span>')
- Terabytes (Eg. '<span style="color:DodgerBlue">1 TB</span>')
- Petabytes (Eg. '<span style="color:DodgerBlue">0.5PB</span>')
- etc...

### Time Format
Accepted time units are:
- s, second
- m, minute
- h, hour
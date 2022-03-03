
### Config description:


#### <span style="color:blue">Sonarr LAN IP Address</span>
The protocol and IP address of the Sonarr application


#### <span style="color:blue">Sonarr API Key</span>
Sonarr application API key


#### <span style="color:blue">Mode</span>

##### Trigger series refresh on task complete
Use this mode when you wish to simply trigger a refresh on a series to re-read a modified file after Unmanic has 
processed it.

##### Import episode on task complete
Use this mode when you are running Unmanic prior to importing a file into Sonarr. 
This will trigger a download import.

If possible, this will associate with a matching queued download and import the file that way. However, it is possibly this will fail.
If it does fail, it will fallback to providing the file path to Sonarr and allowing Sonarr to carry out a normal 
automated import by parsing the file name.

<div style="background-color:pink;border-radius:4px;border-left:solid 5px red;padding:10px;">
<b>Warning:</b>
<br>When configuring a library that will be using this plugin in this "import" mode, it is advised to not include 
the temporary download location within the library path. This may cause Unmanic to collect the incomplete 
download especially with file monitor enabled.
</div>

#### <span style="color:blue">Limit file import size</span>
Only available if the *Import episode on task complete* mode is selected.

Enable limiting the Sonarr notification on items over the value specified in the *Minimum file size* option.


#### <span style="color:blue">Minimum file size</span>
Only available if the *Import episode on task complete* mode, and the *Limit file import size* 
box is selected.

Sizes can be written as:

- Bytes (Eg. '<span style="color:blue">50</span>' or '<span style="color:blue">800 B</span>')
- Kilobytes (Eg. '<span style="color:blue">100KB</span>' or '<span style="color:blue">23 K</span>')
- Megabytes (Eg. '<span style="color:blue">9M</span>' or '<span style="color:blue">34 MB</span>')
- Gigabytes (Eg. '<span style="color:blue">4GB</span>')
- etc...

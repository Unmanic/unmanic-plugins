
For configuration options:
 - [Comskip forum](http://www.kaashoek.com/comskip/)
 - [GitHub](https://github.com/erikkaashoek/Comskip)

---

<div style="background-color:#cfd;border-radius:4px;border-left:solid 5px #2b4;padding:10px;">
<b>Tip:</b>
<br>It is recommended to have this as the very last Plugin in your <b>Worker - Processing file</b></b> flow.
</div>

### Overview

If **Generate chapter information in file metadata** and **Remove detected commercials from file** are unselected in this Plugin's settings,
this Plugin will generate a comskip file according to your configuration in the same directory as the source file.

The name of the generated files will be the same as the video but with a different file extension such as **.edl** or **.txt** (depending on your configuration).

This Plugin will auto-install the required dependencies on container startup. Note that this may cause a slower-than-normal startup of the container the first time and every time it is updated thereafter.

The Plugin does not install the required comskip dependencies on any other system. Ensure you have done this prior to running.


### Config description:

#### <span style="color:blue">Only run when the original source file matches specified extensions</span>
When selected, you may specify a list of file extensions that this Plugin will be limited to processing.

This list is matched against the original source file. Not the current cached file.
For this reason you can remux the original file to another container prior to processing.

Eg: If you limit to `ts` files only and then, in your Plugin flow prior to this Plugin running, another Plugin remuxes
the file `.ts` -> `.mkv`, this Plugin will still process the `.mkv` file.

#### <span style="color:blue">Comskip configuration</span>
Add your comskip.ini configuration here.


#### <span style="color:blue">Generate chapter information in file metadata (Comchap)</span>
Commercial detection script and add chapters original file.
[GitHub](https://github.com/BrettSheleski/comchap)

Comchap will read the input file specified to generate chapter information marking where commercials are located.

Comchap will use your Comskip configuration to do the detection of commercials.


#### <span style="color:blue">Remove detected commercials from file (Comcut)</span>
Commercial detection and removal script.
[GitHub](https://github.com/BrettSheleski/comchap)

Comcut will read the input file specified and remove detected commercials.

Comcut is very similar to Comchap, however the detected commercials are removed from the resulting file. 
Chapters are still added to the resulting file.

<div style="background-color:pink;border-radius:4px;border-left:solid 5px red;padding:10px;">
<b>Warning:</b>
<br>This will modify the file, removing the detected commercials. There is no reversing this process.
<br>Ensure you are happy with your Comskip configuration before letting loose on your library.
</div>





:::warning
Be sure to set the Plugin flow!
See examples below.
:::

---

### Config description:

#### <span style="color:blue">Mark the task as failed</span>
During the worker processing, if this plugin determines that a file is larger than the original file, it will fail the task and no other plugins will be run.

Tasks that fail this way will be marked as failed in the Completed Tasks list.


#### <span style="color:blue">Ignore files in future scans if end result is larger than source</span>
If during post-processing, the final file is determined to be larger than the original file, the source file will be flagged to be ignored for all future library file tests.

If during the worker processing, the file is determined to be larger than the original file and the Mark the task as failed plugin option is enabled, the source file will be flagged to be ignored for all future library file tests.

If during a library scan or file event, a file is found that would otherwise meet the criteria to be added as a new pending task, if that file has been previously flagged to be ignored, then it shall be ignored regardless of the file's status in the Completed Tasks list.


---

#### Examples:

###### <span style="color:magenta">Transcoding to H265 with the NVIDIA NVENC Plugin:</span>
If you are trying to reduce your video library size by converting files to H265, you may want to first attempt to transcode 
a file with the NVENC HEVC encoder to reduce its size.
However, the results of such a conversion may be larger than the source depending on your hardware and configuration.

If you end up with a larger file than the source after using this Plugin, you can use this Plugin to reject the encoded file 
in order to keep the original.

To do this, configure your Plugin Flow as follows:

1. Video Encoder H265/HEVC - hevc_nvenc (NVIDIA GPU)
2. Reject File if Larger than Original (This Plugin)
3. Any other Plugins you wish to run against this library.

**<span style="color:blue">Mark the task as failed</span>**
> *(UNSELECTED)*

**<span style="color:blue">Ignore files in future scans if end result is larger than source</span>**
> *(SELECTED)*

###### <span style="color:magenta">Transcoding to H265 with the NVIDIA NVENC Plugin - Fallback to CPU libx265 if larger:</span>
Almost exactly the same flow as the previous example...
But this time with a re-attempt to transcode using the CPU. 

To do this, set the flow like this:

1. Video Encoder H265/HEVC - hevc_nvenc (NVIDIA GPU)
2. Reject File if Larger than Original (This Plugin)
3. Video Encoder H265/HEVC - libx265 (CPU)
4. Any other Plugins you wish to run against this library.

In this case, the CPU HEVC encoder will re-attempt to transcode the file to HEVC/H265. 
You should get much better results with this encoder, however the time to transcode will be much longer.

**<span style="color:blue">Mark the task as failed</span>**
> *(UNSELECTED)*

**<span style="color:blue">Ignore files in future scans if end result is larger than source</span>**
> *(SELECTED)*

###### <span style="color:magenta">Reject file as the last in the flow (carry out post-processing file movements):</span>
Placing this plugin as the last option in the plugin flow will cause it to simply reset the current working file.
This will not fail the task process.

During post-processing, the original file will be copied to the cache directory and any post-processing tasks can be carried out on that file.
This allows other post-processing plugins to carry out tasks as they otherwise normally would, but on the original file.

**<span style="color:blue">Mark the task as failed</span>**
> *(UNSELECTED)*

**<span style="color:blue">Ignore files in future scans if end result is larger than source</span>**
> *(SELECTED)*

###### <span style="color:magenta">Reject file at any time during worker processing (fail the task - skip post-processing):</span>
Regardless of where this plugin is in the flow, if you select **Mark the task as failed**, it will fail the task and no post-processing file movements will be carried out.

Future library scans will ignore this file, even after you have removed it from the Completed Task list.

**<span style="color:blue">Mark the task as failed</span>**
> *(SELECTED)*

**<span style="color:blue">Ignore files in future scans if end result is larger than source</span>**
> *(SELECTED)*

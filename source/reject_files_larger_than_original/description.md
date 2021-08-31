
Be sure to set the Plugin flow!

---

#### Examples:

###### <span style="color:magenta">Transcoding to HEVC/H265 with the NVIDIA NVENC Plugin:</span>
If you are trying to reduce your video library size by converting files to H265, you may want to first attempt to transcode 
a file with the NVENC HEVC encoder to reduce its size.
However, the results of such a conversion may be larger than the source depending on your hardware and configuration.

If you end up with a larger file than the source after using this Plugin, you can use this Plugin to reject the encoded file 
in order to keep the original.

To do this, configure your Plugin Flow as follows:

1. Video Encoder H265/HEVC - hevc_nvenc (NVIDIA GPU)
2. Reject File if Larger than Original (This Plugin)
3. Any other Plugins you wish to run against this library.

You may also want to re-attempt to transcode using the CPU in such an occasion. To do this, set the flow like this:

1. Video Encoder H265/HEVC - hevc_nvenc (NVIDIA GPU)
2. Reject File if Larger than Original (This Plugin)
3. Video Encoder H265/HEVC - libx265 (CPU)
4. Any other Plugins you wish to run against this library.

In this case, the CPU HEVC encoder will re-attempt to transcode the file to HEVC/H265. 
You should get much better results with this encoder, however the time to transcode will be much longer.

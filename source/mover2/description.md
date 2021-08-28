
Based on the original mover plugin written by [R3dC4p](https://github.com/R3dC4p)


### Config description:

#### <span style="color:blue">Destination directory</span>
Select the destination directory that you wish to have your files moved to

#### <span style="color:blue">Recreate directory structure</span>
This is enabled by default.

When this option is enabled, the directory structure of the source file will be recreated in the destination directory.

This is useful for maintaining directory structure between docker containers.

Disable this if you wish all files to be moved only to the root of the destination directory.

#### <span style="color:blue">Remove source files</span>
This is disabled dy default.

When this option is enabled, the original source file will be removed.

If the file copy process was unsuccessful, then the original source file will be kept regardless of this option being selected or unselected.

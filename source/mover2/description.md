
Based on the original mover plugin written by [R3dC4p](https://github.com/R3dC4p)


### Config description:

#### <span style="color:blue">Destination directory</span>
Select the destination directory that you wish to have your files moved to.

#### <span style="color:blue">Recreate directory structure</span>
This is enabled by default.

When this option is enabled, the directory structure of the source file will be recreated in the destination directory.

This is useful for maintaining directory structure between docker containers.

Disable this if you wish all files to be moved only to the root of the destination directory.

#### <span style="color:blue">Also include library path when re-creating the directory structure</span>
Enabled by default.

When this option is enabled, the full path will be re-created, including the original library path.

If this option is disabled, the library path will be ignored when recreating the directory structure at the destination directory.

#### <span style="color:blue">Remove source files</span>
This is disabled dy default.

When this option is enabled, the original source file will be removed.

If the file copy process was unsuccessful, then the original source file will be kept regardless of this option being selected or unselected.

---

#### Examples:
(examples below are assuming your library path is configured as `/library`)

###### <span style="color:magenta">Move file with full source path and keep original copy</span>
**<span style="color:blue">Destination directory</span>**
> `/processed`

**<span style="color:blue">Recreate directory structure</span>**
> *(SELECTED)*

**<span style="color:blue">Also include library path when re-creating the directory structure</span>**
> *(SELECTED)*

**<span style="color:blue">Remove source files</span>**
> *(UNSELECTED)*

###### Result:
- **Source file path:** <span style="color:green">`/library/tv/MyShow/MyShow-S01E01-720p.mkv`</span>
- **Destination file path:** <span style="color:green">`/processed/library/tv/MyShow/MyShow-S01E01-720p.mkv`</span>

###### <span style="color:magenta">Move file with relative source path and remove original copy</span>
**<span style="color:blue">Destination directory</span>**
> `/processed`

**<span style="color:blue">Recreate directory structure</span>**
> *(SELECTED)*

**<span style="color:blue">Also include library path when re-creating the directory structure</span>**
> *(UNSELECTED)*

**<span style="color:blue">Remove source files</span>**
> *(SELECTED)*

###### Result:
- **Source file path:** <span style="color:red">`/library/tv/MyShow/MyShow-S01E01-720p.mkv`</span> (removed)
- **Destination file path:** <span style="color:green">`/processed/tv/MyShow/MyShow-S01E01-720p.mkv`</span>

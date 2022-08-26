
### Config description:

#### <span style="color:blue">Radarr LAN IP Address</span>
The protocol and IP address of the Radarr application

#### <span style="color:blue">Radarr API Key</span>
Radarr application API key

#### <span style="color:blue">Mode</span>

- **Trigger movie refresh on task complete**
  - Use this mode when you wish to simply trigger a refresh of a movie to re-read a modified file after Unmanic has processed it.
  - **Trigger Radarr file renaming**
    - Trigger Radarr to re-name files according to the defined naming scheme.
    - Useful if you've changed encodings and have these encodings in your Radarr name templates.
    - Only available if the *Trigger movie refresh on task complete* mode is selected.
- **Import movie on task complete**
  - Use this mode when you are running Unmanic **prior** to importing a file into Radarr. This will trigger a download import.
  - If possible, this will associate with a matching queued download and import the file that way. However, it is possible this will fail. If it does fail, it will fallback to providing the file path to Radarr and allowing Radarr to carry out a normal automated import by parsing the file name.
  
    :::warning
    When configuring a library that will be using this plugin in this "import" mode, it is advised to not include the temporary download location within the library path. This may cause Unmanic to collect the incomplete download especially with file monitor enabled.
    :::

  - **Limit file import size**

    :::note
    Only available if the *Import movie on task complete* mode is selected.
    :::

    - Enable limiting the Radarr notification on items over the value specified in the *Minimum file size* option.

  - **Minimum file size**

    :::note
    This option is only available if the *Import movie on task complete* mode, **and** the *Limit file import size* box is selected.
    :::

    - Sizes can be written as:
      - Bytes (Eg. '<span style="color:blue">50</span>' or '<span style="color:blue">800 B</span>')
      - Kilobytes (Eg. '<span style="color:blue">100KB</span>' or '<span style="color:blue">23 K</span>')
      - Megabytes (Eg. '<span style="color:blue">9M</span>' or '<span style="color:blue">34 MB</span>')
      - Gigabytes (Eg. '<span style="color:blue">4GB</span>')
      - etc...

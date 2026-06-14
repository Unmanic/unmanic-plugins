
**<span style="color:#56adda">0.2.3</span>**
- Update runner signatures to accept keyword helper args for Unmanic compatibility

**<span style="color:#56adda">0.2.2</span>**
- Store new metric timestamps in UTC and emit UTC-safe timing data to Unmanic Central
- Return timestamp values to the standalone panel and format them in the viewer's browser timezone

**<span style="color:#56adda">0.2.1</span>**
- Fix the data panel database connection handling and empty-state responses to avoid frontend JSON errors
- Refresh the standalone panel layout, notices, and mobile dialog behaviour
- Improve dark mode, chart theming, and small-screen panel spacing

**<span style="color:#56adda">0.2.0</span>**
- Use new plugin runners to improve data collection (requires Unmanic v0.3.0 or higher)
- Send Unmanic data logs for each post-processed file containing the file size changes (requires Unmanic v0.3.0 or higher)

**<span style="color:#56adda">0.1.1</span>**
- When viewing on mobile, show individual file metrics in a dialog popup

**<span style="color:#56adda">0.1.0</span>**
- New layout to try and make better use of space

**<span style="color:#56adda">0.0.12</span>**
- Correct spacing between the bars on the size charts
- Reduce the height of the top chart area

**<span style="color:#56adda">0.0.11</span>**
- File Size charts now support the dark theme

**<span style="color:#56adda">0.0.10</span>**
- Initial version of dark mode support

**<span style="color:#56adda">0.0.9</span>**
- Update DataTables plugin in preparation of supporting dark mode

**<span style="color:#56adda">0.0.8</span>**
- Update Plugin for Unmanic v2 PluginHandler compatibility

**<span style="color:#56adda">0.0.7</span>**
- Fix issue with number formatting
- Add support for parsing data for tasks processed with remote workers

**<span style="color:#56adda">0.0.6</span>**
- Remove migrations of legacy Unmanic historic data as it still causes intermittent issues
- More improvements to plugin's database connection

**<span style="color:#56adda">0.0.5</span>**
- Improvements to plugin's database connection

**<span style="color:#56adda">0.0.4</span>**
- Fix issue where the Plugin's database was being locked by multiple workers attempting to update at the same time

**<span style="color:#56adda">0.0.3</span>**
- Fix exception and rollback of DB transaction.

**<span style="color:#56adda">0.0.2</span>**
- Set initial flow priority to high

**<span style="color:#56adda">0.0.1</span>**
- Initial version

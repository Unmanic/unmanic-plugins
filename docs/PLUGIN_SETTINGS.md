# The Plugin Settings

The Settings object holds a dictionary of settings accessible to the Plugin
class and able to be configured by users from within the Unmanic WebUI.

This class has a number of methods available to it for accessing these settings:

- ## get_setting({key})
    Fetch a single setting value. Or set "all" as the key argument and return the full dictionary.


- ## set_setting({key}, {value})
    Set a singe setting value.

    Used by the Unmanic WebUI to save user settings.
    
    Settings are stored on disk in order to be persistent.


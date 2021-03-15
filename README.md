# Unmanic Plugins (examples)

Here you will find the documentation required in order to create plugins for [Unmanic](https://github.com/Josh5/unmanic)


## Contents

[Plugin Types](#plugin-types)

[Configuring a Plugin](#configuring-a-plugin)

[Testing a Plugin](#testing-a-plugin)

[License and Contribution](#license-and-contribution)


---
## Plugin Types

Currently the following plugin types are available:

| Type     |                    Information                     |  
|----------|:--------------------------------------------------:|
| Worker   |  [Worker Plugin Docs](docs/plugin-types/WORKER.md) |

Plugins are modules that consist of a `plugin.py` file containing one or more `"runners"`.

A plugin runner is a function conforming to a particular name that is executed at defined 
stages during the Unmanic file workflow.
For more information on the different types of plugin runners, refer to the individual 
plugin docs listed above.


---
## Configuring a Plugin

Plugins can be configured using the plugin's settings class.
See [Plugin Settings Docs](docs/PLUGIN_SETTINGS.md)


---
## Testing a Plugin

There are a series of tools available to develop a plugin for Unmanic.

See [Testing Plugins Docs](docs/TESTING_PLUGINS.md)


---
## License and Contribution

This projected is licensed under th GPL version 3. 

Copyright (C) Josh Sunnex - All Rights Reserved

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
 
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

This project contains libraries imported from external authors.
Please refer to the source of these libraries for more information on their respective licenses.

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) to learn how to contribute to Unmanic.

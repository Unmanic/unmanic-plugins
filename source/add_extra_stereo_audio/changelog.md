
**<span style="color:#56adda">0.0.13</span>**
- fix stream_to_stereo_encode so it doesn't identify incorrect stream in case of files with mixture of tagged and untagged languages

**<span style="color:#56adda">0.0.12</span>**
- make commentary check a substring test
- added missing language check in case where channels or codec_name are left blank

**<span style="color:#56adda">0.0.11</span>**
- add option to move stereo stream to first audio stream
- remove setting of add to task list of False so subsequent plugins will execute
- add iso639 module to get language name from code
- add metadata stream title to stereo stream based on language, codec, and "STEREO"

**<span style="color:#56adda">0.0.10</span>**
- fix stream to encode to guard against streams with no audio language tags

**<span style="color:#56adda">0.0.9</span>**
- unspecified stream parameters now can only be channels and codec, language must be specified

**<span style="color:#56adda">0.0.8</span>**
- add fix to ignore commentary streams

**<span style="color:#56adda">0.0.7</span>**
- add fix to avoid KeyError when language tag doesn't exist

**<span style="color:#56adda">0.0.6</span>**
- add option to set default audio to new stereo audio channel

**<span style="color:#56adda">0.0.5</span>**
- add option to remove multichannel audio stream

**<span style="color:#56adda">0.0.4</span>**
- fix file scan test audio stream counter

**<span style="color:#56adda">0.0.3</span>**
- add separate loop test for existing 2 channel stereo streams

**<span style="color:#56adda">0.0.2</span>**
- fix file scan test to ignore files that already have a 2 channel, stereo aac stream

**<span style="color:#56adda">0.0.1</span>**
- initial release

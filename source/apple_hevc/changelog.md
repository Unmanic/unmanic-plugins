
**<span style="color:#56adda">0.0.2</span>**
- Fix file test crashing with AttributeError when the file probe fails (Probe.init_probe returns None)
- Fix thread race: only call mimetypes.init() once (concurrent library-scan file testers could see guess_type() return None for valid files, silently skipping them)

**<span style="color:#56adda">0.0.1</span>**
- initial version

---
description: List all connected Android physical devices and available emulators (AVDs)
---

Run the following commands and present a combined numbered list:

```bash
adb devices -l
```
```bash
$ANDROID_HOME/emulator/emulator -list-avds 2>/dev/null || emulator -list-avds 2>/dev/null
```

Parse the output and return a formatted numbered list:

```
Android Devices & Emulators
════════════════════════════
Physical Devices:
  [1] <serial>  <model>  API <level>  (<state>)

Emulators (AVDs):
  [2] <avd-name>  (not running)
  [3] <avd-name>  (running - <serial>)

Total: X physical, Y emulators
```

Rules:
- Skip the `* daemon started` lines from adb output
- If `adb` is not found → tell the user Android SDK is not configured and to run `/start-session` first
- If no devices are connected → say "No Android devices connected. Connect a device via USB with USB debugging enabled, or start an emulator."
- Store the list in session memory so the user can reference devices by index in subsequent commands

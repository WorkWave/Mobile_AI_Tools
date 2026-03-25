---
description: List all connected iOS physical devices and available simulators
---

Run the following command and parse the output:

```bash
xcrun xctrace list devices 2>/dev/null
```

Also check running simulators:
```bash
xcrun simctl list devices available 2>/dev/null
```

Return a formatted numbered list:

```
iOS Devices & Simulators
═════════════════════════
Physical Devices:
  [1] iPhone 14 Pro  (00008110-XXXXXXXXXXXX)  iOS 17.2

Simulators:
  [2] iPhone 15 Pro  (XXXXXXXX-XXXX-XXXX-XXXX)  iOS 17.2  [Booted]
  [3] iPhone 14      (XXXXXXXX-XXXX-XXXX-XXXX)  iOS 16.4  [Shutdown]
  [4] iPad Air (5th gen)  (XXXXXXXX-XXXX-XXXX-XXXX)  iOS 17.2  [Shutdown]

Total: X physical, Y simulators
```

Rules:
- If `xcrun` is not found → tell the user Xcode is not installed and to run `/start-session` first
- Show [Booted] for running simulators, [Shutdown] for available but not running
- If no physical devices are found → note "No physical iOS devices connected. Connect via USB and trust this Mac."
- Store the list in session memory so the user can reference devices by index

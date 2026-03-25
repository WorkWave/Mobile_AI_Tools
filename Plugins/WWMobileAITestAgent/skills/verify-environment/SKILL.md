---
name: verify-environment
description: Check that all required dependencies for mobile testing are installed (Xcode, Android SDK, Java, Node, Python, Appium, Firebase CLI). Offer guided installation for missing tools. Also verify Atlassian and Figma MCP servers are configured.
---

# Environment Verification

Check each dependency below. For each one, run the check command, capture the version if installed, and build a report.

## Dependency Checks

Run ALL checks in parallel using Bash:

| Tool | Check Command | Critical |
|------|---------------|----------|
| Python 3.11+ | `python3 --version` | Yes |
| Java JDK 11+ | `java -version 2>&1` | Yes |
| Node.js 18+ | `node --version` | Yes (Appium needs it) |
| Xcode | `xcode-select -p` | iOS only |
| Android SDK (adb) | `adb --version 2>/dev/null \|\| $ANDROID_HOME/platform-tools/adb --version 2>/dev/null` | Android only |
| Appium 2.x | `appium --version` | Yes |
| Appium UIAutomator2 | `appium driver list 2>/dev/null \| grep "uiautomator2.*installed"` | Android |
| Appium XCUITest | `appium driver list 2>/dev/null \| grep "xcuitest.*installed"` | iOS |
| Firebase CLI | `firebase --version` | Yes |
| ios-deploy | `ios-deploy --version` | No (optional — Appium XCUITest handles install) |

## Report Format

Display a clear table:

```
Environment Check
══════════════════════════════════════════════════
✅  Python        3.11.8
✅  Java          17.0.9
✅  Node.js       20.11.0
✅  Appium        2.4.1
❌  Xcode         NOT FOUND
⚠️  ios-deploy    NOT FOUND  (needed for physical iOS)
✅  Firebase CLI  13.0.2
✅  Android SDK   34.0.4
✅  UIAutomator2  installed
✅  XCUITest      installed
══════════════════════════════════════════════════
```

## MCP Server Check

Check if Atlassian and Figma MCP servers are active:
- Look for `mcp__claude_ai_Atlassian__` tools in the current session
- Look for `mcp__claude_ai_Figma__` tools in the current session

If either is missing, show:
```
⚠️  Atlassian MCP: NOT CONFIGURED
    Add to Claude settings > MCP Servers:
    {
      "claude.ai Atlassian": {
        "type": "http",
        "url": "https://mcp.atlassian.com/v1/mcp"
      }
    }

⚠️  Figma MCP: NOT CONFIGURED
    Add to Claude settings > MCP Servers:
    {
      "claude.ai Figma": {
        "type": "http",
        "url": "https://mcp.figma.com/v1/mcp"
      }
    }
```

## Missing Tool Handling

For each missing critical tool, ask the user once:

```
❌ <ToolName> is not installed.
   Install command: <brew/npm install command>
   Do you want me to install it now? (yes/no)
```

- If **yes** → run the install command, re-check after
- If **no** → note it and continue; mark it as SKIPPED
- If any CRITICAL tool is declined → warn: "Some tests may not work without <tool>."

## Install Commands

| Tool | Install Command |
|------|-----------------|
| Python 3.11 | `brew install python` |
| Java 17 | `brew install openjdk@17` |
| Node.js | `brew install node` |
| Xcode | "Install from Mac App Store, then run: `sudo xcode-select --switch /Applications/Xcode.app`" |
| Appium | `npm install -g appium` |
| UIAutomator2 | `appium driver install uiautomator2` |
| XCUITest | `appium driver install xcuitest` |
| Firebase CLI | `npm install -g firebase-tools` |
| ios-deploy | `brew install ios-deploy` |
| Android SDK | "Install Android Studio from developer.android.com, then set ANDROID_HOME in your shell profile" |

After completing all checks, return a summary:
- List of installed tools with versions
- List of missing/skipped tools
- Whether MCP servers are configured
- Overall status: READY / READY WITH WARNINGS / NOT READY

---
name: automated-screen-discovery
description: After login, systematically explore the running app via Appium to map all screens, navigation hierarchy, and interactive elements. Saves to appium_navigation_map_<platform>.json, then merges into navigation_map_<platform>.json. Skip if map already exists and app commit hash hasn't changed.
---

> **Session data:** Read `OUTPUT_DIR`, `project`, `platform`, `udid`, and `config` from session memory (set by session-wizard). If any value is missing → load from `$OUTPUT_DIR/<project>/config.json` directly before proceeding.

## Pre-flight Check

1. Read `platform` from session memory (ios or android)
2. Check if `$OUTPUT_DIR/<project>/nav_maps/appium_navigation_map_<platform>.json` exists
3. If it does, ask:
```
An Appium navigation map already exists for <platform> (last analyzed: <date>, <N> screens).
Update it? (yes/no)
```
If no → skip this skill entirely.

---

## Step 1 — Start Appium Session

Use `mcp__appium__create_session` with:
- `platformName`: Android or iOS (from session)
- `deviceName`: from session
- `udid`: from session
- `bundleId` / `appPackage`: from `config.json`
- `automationName`: UIAutomator2 (Android) or XCUITest (iOS)
- iOS physical: add `appium:xcodeOrgId` and `appium:derivedDataPath` if WDA was already built

---

## Step 2 — Login

### Permission Popup Handler (call after EVERY tap or navigation)
```
Check for: //XCUIElementTypeButton[@name="Allow"]
           //XCUIElementTypeButton[@name="Allow While Using App"]
           //XCUIElementTypeButton[@name="OK"]
           //XCUIElementTypeButton[@name="Continue"]
           //XCUIElementTypeButton[@name="Not Now"]
```
If found → tap it immediately. On Android: use `mcp__appium__handle_alert` to accept.

### Fill Login Fields — Xamarin/MAUI-safe strategy

For each field in `authSchema.fields`:

1. **Tap to focus** using `mcp__appium__appium_click`, wait 1s
2. **Strategy A — set_value + verify:**
   - Call `mcp__appium__appium_set_value` with the value
   - Call `mcp__appium__appium_get_text` on the same element
   - If returned text matches the value → continue to next field
   - If NOT → Strategy B
3. **Strategy B — keyboard key taps** (Xamarin binding fallback):
   - Find keyboard keys via `//XCUIElementTypeKey[@name="<char>"]` and tap each one
   - After all chars typed, tap `//XCUIElementTypeButton[@name="Return"]` or `[@name="Next"]`
4. **Strategy C — manual fallback:**
   - Ask user: "Please type `<value>` in the `<fieldName>` field on the device, then press Enter here."

After filling all fields:
- Run permission popup handler
- **Move focus to next field** (tap it) to trigger `EditingDidEnd` Xamarin binding on previous field
- After last field, tap the login/submit button
- Run permission popup handler
- Poll every 2s (max 20s) for home screen: login succeeded when login fields are no longer present

If login fails → report: "Login failed. Check credentials or network." and stop.

---

## Step 3 — Fast Systematic Exploration

### Speed Rules (critical — follow strictly)
- No screenshots — they are slow and not needed for the nav map
- One `get_page_source` per screen — parse everything from it, never call it twice for the same screen
- 2s wait after each tap (not 5s or 10s)
- Skip screen if it matches a title already visited — the visited set is the only loop guard
- Skip non-navigable elements: images, static text, dividers, disabled buttons

### Exploration Algorithm

```
visited = set()
queue = [tab_bar_items]

for each item in queue:
  1. tap item (mcp__appium__appium_click)
  2. wait 2s
  3. run permission popup handler
  4. get_page_source ONCE → parse:
       - screen_title: first StaticText or NavigationBar title
       - tabs: XCUIElementTypeTab / android tab elements
       - buttons: XCUIElementTypeButton with meaningful names (len > 2, not icons)
       - cells: XCUIElementTypeCell (list items that navigate)
       - menu_items: named interactive elements
  5. if screen_title already in visited → go back, skip
  6. record screen (see format below)
  7. visited.add(screen_title)
  8. add navigable buttons/cells to queue (max 5 per screen)
  9. go back: iOS = swipe right from x=20, or tap Back button
              Android = mcp__appium__mobile_press_key BACK
```

### Element filtering rules
Only add to queue if element:
- Is a `XCUIElementTypeButton` or `XCUIElementTypeCell` with `enabled="true"`
- Has a `name` attribute length > 2
- Name does NOT contain: `ic_`, `img_`, `icon`, `divider`, `separator`
- Name is NOT: `Log In`, `Not Now`, `Cancel`, `Close`, `Back`, `Allow`, `OK`

---

## Step 4 — Save to appium_navigation_map_<platform>.json

Write to `$OUTPUT_DIR/<project>/nav_maps/appium_navigation_map_<platform>.json` (where `<platform>` is `ios` or `android` from session memory):

```json
{
  "project": "<project>",
  "last_analyzed": "<ISO date>",
  "commit_hash": "<git hash if available>",
  "discovery_method": "automated",
  "platform": "<android|ios>",
  "total_screens": N,
  "architecture": {
    "navigation_type": "tab_bar | drawer | stack | mixed",
    "tab_bar_items": ["Jobs", "Call Logs", "TimeSheets", "More"]
  },
  "authentication": {
    "type": "custom",
    "fields": ["companyNumber", "employeeId", "password"]
  },
  "screens": {
    "Jobs": {
      "path": "launch → login → Jobs tab",
      "parent": null,
      "tab": "Jobs",
      "prerequisites": ["login"],
      "interactive_elements": ["ic filter", "ic joblist menu", "Daily Checklist"]
    }
  }
}
```

---

## Step 5 — Merge into navigation_map_<platform>.json

Check what exists in `$OUTPUT_DIR/<project>/nav_maps/`:

**If `codebase_navigation_map_<platform>.json` also exists → merge both:**

Merge strategy:
- Start from `codebase_navigation_map_<platform>.json` as base (richer structure: native navigation type, class names, paths)
- For each screen in `appium_navigation_map_<platform>.json`:
  - If screen exists in codebase map → enrich `interactive_elements` with appium findings, keep codebase `path`/`navigation_type`/`class`
  - If screen exists only in appium → add it to the merged map with a note `"source": "appium_only"`
- For screens only in codebase → keep as-is with `"source": "codebase_only"`
- Set `"discovery_method": "merged"`, `"last_analyzed": <now>`, `"total_screens": <combined count>`, `"platform": "<platform>"`

**If `navigation_map_<platform>.json` exists but NO `codebase_navigation_map_<platform>.json` → smart update:**

Do NOT overwrite. Merge the new appium findings into the existing map:

**Per-screen rules:**
| Field | Rule |
|---|---|
| `path` | Keep existing — may be manually curated or from codebase discovery |
| `parent` | Keep existing |
| `prerequisites` | Keep existing |
| `tab` | Keep existing |
| `route` / `viewmodel` | Keep existing — never overwrite code-derived fields |
| `source` | Keep existing (e.g. `"codebase_only"`) unless screen is new from appium |
| `interactive_elements` | **Union**: add new appium elements not already in the list, keep all existing ones |
| Any unknown extra fields | Keep as-is |

**Screen presence rules:**
- Screen exists in both → apply per-field rules above
- Screen only in new appium map → add it with `"source": "appium_only"`
- Screen only in existing `navigation_map_<platform>.json` → keep as-is, do NOT remove

**Top-level fields to update:**
- `last_analyzed` → update to now
- `total_screens` → recalculate from merged screen count
- `discovery_method` → set to `"appium_updated"`
- `architecture.tab_bar_items` → union with new tabs found (add any new ones, keep existing)
- `commit_hash` → update if a newer hash is available

**If `navigation_map_<platform>.json` does NOT exist and no codebase map either:**

Copy `appium_navigation_map_<platform>.json` as-is to `navigation_map_<platform>.json`.

**Write result to `$OUTPUT_DIR/<project>/nav_maps/navigation_map_<platform>.json`.**

---

## Step 6 — Close Session

Call `mcp__appium__delete_session`.

Report:
```
✅ Appium screen discovery complete
   Screens mapped   : N
   Appium map saved : $OUTPUT_DIR/<project>/nav_maps/appium_navigation_map_<platform>.json
   Nav map updated  : $OUTPUT_DIR/<project>/nav_maps/navigation_map_<platform>.json  (merged | copied)
```

---
name: workflow-test
description: Execute a structured test workflow from a markdown file in $OUTPUT_DIR/<project>/test-workflow/. Creates a starter file if none exists. Runs each phase sequentially via Appium.
---
> **Session data:** Read `OUTPUT_DIR`, `project`, `platform`, `udid`, and `config` from session memory (set by session-wizard). If any value is missing → load from `$OUTPUT_DIR/<project>/config.json` directly before proceeding.


# test-workflow

## Output Folders

Test definition files (markdown):
```
$OUTPUT_DIR/<project>/test-workflow/
```

Generated reusable scripts:
```
$OUTPUT_DIR/<project>/auto-generated-scripts/workflow-tests-scripts/
├── ios/
│   └── <workflow_filename>.py
└── android/
    └── <workflow_filename>.py
```

## Step 1 — Check for Existing Test Files

List all `.md` files in `$OUTPUT_DIR/<project>/test-workflow/`.

**If none exist** → create the starter file automatically using the navigation map (see Starter File Template below), then tell the user:
```
No test files found. I've created a starter file using the navigation map:
  $OUTPUT_DIR/<project>/test-workflow/full-app-workflow.md

You can edit it to add your test phases, then re-run this mode.
Shall I execute the starter file now? (yes/no)
```

**If exactly one file exists** → skip the "Run ALL" option (it's redundant with a single file) and show:
```
<Project> selected. Test files available:

  [1] <filename>.md
  [2] Add new test file

Select an option (1-2):
```

**If more than one file exists** → show the full menu including "Run ALL":
```
<Project> selected. Test files available:

  [1] Run ALL files sequentially
  [2] <first_file>.md
  [3] <second_file>.md
  ...
  [N] Add new test file

Select an option (1-N):
```

**If [1] — Run ALL (only shown when multiple files exist):**
- Run each file in sequence (steps 2–6 for each)
- Before each file: check if an Appium session is already active
  - If active and app is on home screen → reuse session (skip login)
  - If not active or on login screen → create new session and login
- After each file: generate its autoscript (Step 6) and show its phase summary
- After all files: generate a single combined `qa-report` covering all workflows

**If a file is selected — Single run:**
- Proceed normally from Step 2 with that file only

## Starter File Template

```markdown
# Full App Workflow — <Project>

## Phase 1: App Launch
- Open the app for the first time (fresh install)
- Wait for the splash screen (max 5s)
- Handle any permission dialogs (Location, Notifications) — tap Allow
- Verify the login screen is visible

## Phase 2: Login
- Enter <field1_label>: <placeholder>
- Enter <field2_label>: <placeholder>
- [if 3 fields] Enter <field3_label>: <placeholder>
- Tap the Login / Sign In button
- Wait for the home screen to load (max 15s)
- Verify the home screen title or main navigation is visible

## Phase 3: Home Screen
- Verify the main navigation elements are present
- Verify no error banners or crash dialogs are shown
- Take a screenshot for baseline

## Phase 4: Navigation Smoke
- Navigate to each main tab / menu section
- Verify each section loads without error
- Go back to home after each

## Phase 5: Logout
- Navigate to the profile / settings section
- Tap Logout
- Verify the login screen is shown again
```

## Step 2 — Parse the Test File

Read the selected markdown file. Parse into phases:
- Each `## Phase N: <Name>` → a test phase
- Each `- <step>` → a test step within the phase

## Step 3 — Start Appium Session — Speed-Optimized

Before executing any phase, create the session with speed-optimized capabilities.
Read platform from session memory (set by session wizard).

**iOS:**
```python
capabilities = {
    "platformName": "iOS",
    "appium:automationName": "XCUITest",
    "appium:udid": "<udid>",
    "appium:bundleId": "<bundleId>",
    "appium:noReset": True,
    "appium:newCommandTimeout": 300,
    "appium:webDriverAgentUrl": "http://127.0.0.1:8100",
    "appium:usePrebuiltWDA": True,
    "appium:wdaLaunchTimeout": 30000,
    "appium:wdaConnectionTimeout": 30000,
    "appium:autoAcceptAlerts": True,    # dismiss ALL system permission dialogs immediately
    "appium:implicitWaitTimeout": 5000,
}
```

**Android:**
```python
capabilities = {
    "platformName": "Android",
    "appium:automationName": "UIAutomator2",
    "appium:udid": "<udid>",
    "appium:noReset": True,
    "appium:newCommandTimeout": 300,
    "appium:autoGrantPermissions": True,  # grant ALL runtime permissions automatically
    "appium:skipUnlock": True,
    "appium:implicitWaitTimeout": 5000,
}
```

### Permission Safety Net

After EVERY tap or navigation, run:

**iOS (app-level dialogs not caught by autoAcceptAlerts):**
```python
for btn in ["Allow", "Allow While Using App", "Allow Once", "OK", "Continue", "Got It", "Not Now"]:
    el = find_element("accessibility id", btn, timeout=1)
    if el: el.click(); break
```
**Android:** `autoGrantPermissions: True` handles all cases — no extra check needed.

## Step 4 — Execute Each Phase

**Speed Rules:**
- **No `get_page_source`** — use targeted `find_element`; page source is slow
- **Max 5s wait per element** — mark FAIL immediately if not found, continue
- **Screenshots only on FAIL** and at phase end — never mid-step on PASS
- **Screenshots: always pass `maxWidth: 150`** to `mcp__appium__appium_screenshot` — the full HTML viewer is ~10k tokens and fills context fast
- **Back navigation** — Back button only, never swipe right (Xamarin/MAUI edge gesture conflict)

Before starting each phase, print its title:
```
══════════════════════════════════════════════
  🧪 NOW TESTING — Phase N: <Phase Title>
══════════════════════════════════════════════
```

For each phase, for each step:

1. Interpret the step as an Appium action:
   - "Open the app" → launch via bundle ID
   - "Wait for X (max Ys)" → wait for element, max Y seconds (hard cap 5s unless explicitly longer)
   - "Handle permission dialog — tap Allow" → `autoAcceptAlerts` covers it; safety net as fallback
   - "Enter <field>: <value>" → find by AccessibilityId, clear, send_keys
   - "Tap <button>" → find by AccessibilityId, click, run permission safety net
   - "Verify <condition>" → find element (5s timeout), assert visible
   - "Navigate to <section>" → follow navigation_map path via go_to_tab or navigation helpers
   - "Take a screenshot" → save to `$OUTPUT_DIR/<project>/reports/screenshots/`

2. Log after each step: ✅ PASS or ❌ FAIL + screenshot path

3. On FAIL:
   - Capture screenshot
   - Log the finding
   - Ask: "Step failed: '<step>'. Continue? (yes/no/skip phase)"

## Step 5 — Phase Summary

After each phase:
```
Phase 2: Login ─ 6/6 steps passed ✅
Phase 3: Home Screen ─ 2/3 steps passed ⚠️
  ❌ Step 3: element 'home_title' not found
```

## Step 6 — Generate Autoscript

After all phases complete, generate a Python script and save to:

- iOS:     `$OUTPUT_DIR/<project>/auto-generated-scripts/workflow-tests-scripts/ios/<workflow_filename>.py`
- Android: `$OUTPUT_DIR/<project>/auto-generated-scripts/workflow-tests-scripts/android/<workflow_filename>.py`

`<workflow_filename>` = `.md` filename without extension, spaces replaced with `_`
(e.g. `full-app-workflow.md` → `full_app_workflow.py`)

Ensure `auto-generated-scripts/helpers/` shared files exist. Create if missing, never overwrite.

If the script already exists → overwrite (latest run is the most accurate).

### Script Format

```python
"""
Auto-generated from : <workflow_filename>.md
Platform            : ios | android
Generated           : <YYYY-MM-DD HH:MM>
Build               : v<version> (build <buildNumber>)
Device              : <deviceName> (<udid>)
Account             : <account label>

To rerun on a new build: update UDID / BUNDLE_ID at the top.
Run: python <workflow_filename>.py
"""
import sys, os, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, ROOT)

# iOS imports — replace with android equivalents for Android
from helpers.session import delete_all_sessions, find, tap, set_value, screenshot
from helpers.ios.session import create_session
from helpers.ios.permissions import dismiss_permissions
from helpers.login import login
from helpers.navigation import go_to_tab, go_back

UDID      = "<udid>"
BUNDLE_ID = "<bundleId>"       # iOS only; Android uses APP_PACKAGE + APP_ACTIVITY
PLATFORM  = "ios"
CREDS     = <credentials_dict>
SHOTS     = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SHOTS, exist_ok=True)

RESULTS = {}

def log(phase, step, result, note=""):
    icon = "✅" if result == "PASS" else "❌"
    print(f"  {icon} [{phase}] {step}" + (f" — {note}" if note else ""))
    r = RESULTS.setdefault(phase, {"passed": 0, "failed": 0, "steps": []})
    r["passed" if result == "PASS" else "failed"] += 1
    r["steps"].append({"step": step, "result": result, "note": note})

# ── Phases — filled from actual Appium interactions ────────────────────────────

def phase_1_app_launch(S):
    """Phase 1: App Launch"""
    dismiss_permissions(S)
    # <GENERATED_STEPS>

def phase_2_login(S):
    """Phase 2: Login"""
    login(S, CREDS, platform=PLATFORM)
    dismiss_permissions(S)
    # <GENERATED_STEPS>

# <additional phase functions here>

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Running: <workflow_filename> [{PLATFORM.upper()}]")
    delete_all_sessions()
    S = create_session(UDID, BUNDLE_ID)
    dismiss_permissions(S)
    time.sleep(0.5)

    phase_1_app_launch(S)
    phase_2_login(S)
    # <call additional phases>

    print("\n── Results ──────────────────────────────────")
    total_p = total_f = 0
    for phase, data in RESULTS.items():
        p, f = data["passed"], data["failed"]
        total_p += p; total_f += f
        print(f"  {'✅' if f == 0 else '⚠️'} {phase}: {p}/{p+f}")
    print(f"\nTotal: {total_p}/{total_p+total_f} steps passed")

if __name__ == "__main__":
    main()
```

**Script generation rules:**
- Replace each `# <GENERATED_STEPS>` with the exact `find()`, `tap()`, `set_value()` calls executed during the live test
- FAILed steps: include + add `# ⚠️ FAILED: <reason>` comment + `screenshot()` call
- If the file already exists → overwrite

## Step 7 — Generate Report

After all phases, use `qa-report` skill to generate the full report.

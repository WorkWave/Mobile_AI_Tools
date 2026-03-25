---
name: ticket-test
description: Test a specific Jira ticket. Fetches description and Acceptance Criteria via Atlassian MCP, retrieves Figma design if linked, identifies affected screens via GitHub branch diff, then drives Appium to test each AC. Offers regression at the end.
---
> **Output directory:** Read `OUTPUT_DIR` from session memory (set by session-wizard Step 0). Use `$OUTPUT_DIR/<project>/` for all file paths instead of `projects/<project>/`.


# Ticket-Driven Test

## Step 1 — Fetch Jira Ticket

Ask: "Enter the Jira ticket ID (e.g. PROJ-1234):"

Use Atlassian MCP:
```
mcp__claude_ai_Atlassian__getJiraIssue({ issueIdOrKey: "<ticket>" })
```

Extract:
- **Title** — summary field
- **Description** — full description
- **Acceptance Criteria** — look for AC section in description (search for "Acceptance Criteria", "AC:", "Definition of Done")
- **Status** — current ticket status
- **Assignee**

If the ticket is not found → "Ticket <ID> not found. Check the ID and try again."

## Step 2 — Find Figma Design

Search the ticket description and remote links for `figma.com` URLs:
```
mcp__claude_ai_Atlassian__getJiraIssueRemoteIssueLinks({ issueIdOrKey: "<ticket>" })
```

If a Figma URL is found:
```
mcp__claude_ai_Figma__get_design_context({ fileKey: "<key>", nodeId: "<nodeId>" })
```

Extract: component layout, expected states, color/typography specs.
Display: "📐 Figma design loaded — <N> components found"

If no Figma link → continue without design context.

## Step 3 — Identify Affected Screens

Use the Atlassian MCP development panel to find the linked branch:
```
mcp__claude_ai_Atlassian__fetchAtlassian({
  url: "https://<domain>.atlassian.net/rest/dev-status/latest/issue/detail?issueId=<id>&applicationType=GitHub&dataType=branch"
})
```

If a branch is found (e.g. `feature/PROJ-1234-new-schedule-view`):

Use a subagent to:
1. `git -C <localRepoPath> fetch origin`
2. `git -C <localRepoPath> diff origin/dev...origin/<branch> --name-only`
3. Identify changed files and map them to screens in `navigation_map.json`
4. Create a temporary navigation patch for this session (do NOT overwrite navigation_map.json)

Show:
```
Affected screens detected from branch diff:
  - ScheduleView (route: Scheduling/DayView)
  - NewJobModal  (route: Jobs/Create)
```

If no branch found → use the ticket title/description keywords to search navigation_map.json for likely screens.

## Step 4 — Parse Acceptance Criteria

Parse each AC as a testable step. If ACs are not clearly formatted, ask:
```
I couldn't find clearly structured Acceptance Criteria in this ticket.
Please paste the ACs here, one per line:
```

Number each AC:
```
AC #1: User can tap "New Job" from the schedule view
AC #2: The job creation form shows required fields: customer, date, service type
AC #3: Tapping "Save" with empty required fields shows inline validation errors
AC #4: Successfully saved job appears in the schedule view
```

## Step 5 — Drive Appium Tests

### Session Creation — Speed-Optimized

Start Appium session (if not already active) using speed-optimized capabilities:

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
    "appium:autoAcceptAlerts": True,    # auto-dismiss ALL system permission dialogs
    "appium:implicitWaitTimeout": 5000,
}
```

**Android:**
```python
capabilities = {
    "platformName": "Android",
    "appium:automationName": "UIAutomator2",
    "appium:udid": "<udid>",
    "appium:appPackage": "<appPackage>",
    "appium:appActivity": "<mainActivity>",
    "appium:noReset": True,
    "appium:newCommandTimeout": 300,
    "appium:autoGrantPermissions": True,  # auto-grant ALL runtime permissions
    "appium:implicitWaitTimeout": 5000,
    "appium:skipUnlock": True,
}
```

### Speed Rules (follow strictly during test execution)

- **No `get_page_source` for assertions** — use targeted `find_element`; page source is slow
- **No screenshots mid-flow** — only on FAIL or at AC end
- **Screenshots: always pass `maxWidth: 150`** to `mcp__appium__appium_screenshot` — the full HTML viewer is ~10k tokens and fills context fast
- **Locator priority:** `AccessibilityId` > `resource-id` (Android) > `name` (iOS XPath) > `XPath`
- **Max 5s wait per element** — if not found, mark BLOCKED and move on
- **Back navigation** — always use Back button, never swipe right (Xamarin/MAUI edge gesture conflict)
- **No sleep()** — use `WebDriverWait` with expected conditions

### Permission Dialog Safety Net

`autoAcceptAlerts`/`autoGrantPermissions` handles system-level dialogs. For app-level dialogs run this after every tap or navigation:

**iOS:**
```python
for btn in ["Allow", "Allow While Using App", "Allow Once", "OK", "Continue", "Got It", "Not Now"]:
    el = find_element("accessibility id", btn, timeout=1)
    if el: el.click(); break
```
**Android:** covered by `autoGrantPermissions: True`.

### Test Execution

For each AC:
1. Navigate to the affected screen using the navigation path from `navigation_map.json`
2. Perform the action described in the AC
3. Assert the expected outcome using targeted element finds
4. Run permission safety net if navigation triggered a new screen

Record: **PASS** / **FAIL** (screenshot + log) / **BLOCKED** (timeout 5s)

If behavior is ambiguous:
```
AC #N is ambiguous: what is the expected outcome?
(a) Specific message/element from Figma
(b) Any visible error indicator is acceptable
(c) Skip this AC
```

## Step 5b — Generate and Save Autoscripts

After all ACs are tested, generate Python/Appium scripts and save to the project's
`auto-generated-scripts/` folder.

### Folder Structure

```
$OUTPUT_DIR/<project>/auto-generated-scripts/
├── helpers/
│   ├── session.py        ← platform-agnostic utilities: find, tap, tap_coords,
│   │                        set_value, get_text, screenshot, delete_all_sessions
│   ├── login.py          ← login flow (platform-aware, detects iOS/Android internally)
│   └── navigation.py     ← common navigation helpers: go_to_tab, go_back (platform-aware)
│   ├── ios/
│   │   ├── session.py    ← iOS session factory (WDA, XCUITest, autoAcceptAlerts)
│   │   └── permissions.py ← iOS app-level permission safety net
│   └── android/
│       ├── session.py    ← Android session factory (UIAutomator2, autoGrantPermissions)
│       └── permissions.py ← Android stub (autoGrantPermissions handles most cases)
└── ticket-tests-scripts/
    ├── ios/
    │   └── <TICKET_ID>/
    │       ├── test_<TICKET_ID>.py
    │       └── conftest.py
    └── android/
        └── <TICKET_ID>/
            ├── test_<TICKET_ID>.py
            └── conftest.py
```

**Rules:**
- `helpers/session.py`, `helpers/login.py`, `helpers/navigation.py` are shared across iOS and Android — do NOT duplicate platform logic there, use platform detection (`platform` param or capability check)
- Platform-specific session factories live in `helpers/ios/` and `helpers/android/`
- If a helper file already exists → do NOT overwrite; append new functions only
- Ticket scripts go in the platform subfolder matching the current test session (`ios/` or `android/`)
- If a ticket script already exists → overwrite (latest run is most accurate)

### helpers/session.py — Platform-Agnostic Utilities

```python
"""Platform-agnostic Appium utilities shared across iOS and Android."""
import requests, time, base64, os

APPIUM_URL = "http://127.0.0.1:4723"

def delete_all_sessions():
    """Clean up all stale sessions before starting a new one."""
    try:
        r = requests.get(f"{APPIUM_URL}/sessions", timeout=5)
        for s in r.json().get("value", []):
            requests.delete(f"{APPIUM_URL}/session/{s['id']}", timeout=5)
    except Exception:
        pass

def find(session_id: str, strategy: str, selector: str, timeout: int = 5):
    """Find element with polling timeout. Returns element ID or None."""
    base = f"{APPIUM_URL}/session/{session_id}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.post(f"{base}/element",
            json={"using": strategy, "value": selector}, timeout=5)
        d = r.json().get("value", {})
        eid = d.get("ELEMENT") or d.get("element-6066-11e4-a52e-4f735466cecf")
        if eid:
            return eid
        time.sleep(0.3)
    return None

def tap(session_id: str, element_id: str):
    requests.post(f"{APPIUM_URL}/session/{session_id}/element/{element_id}/click",
        json={}, timeout=5)

def tap_coords(session_id: str, x: int, y: int):
    requests.post(f"{APPIUM_URL}/session/{session_id}/actions", json={"actions": [{
        "type": "pointer", "id": "f1",
        "parameters": {"pointerType": "touch"},
        "actions": [
            {"type": "pointerMove", "duration": 0, "x": x, "y": y},
            {"type": "pointerDown", "button": 0},
            {"type": "pause", "duration": 80},
            {"type": "pointerUp", "button": 0}
        ]
    }]}, timeout=5)

def set_value(session_id: str, element_id: str, value: str):
    requests.post(f"{APPIUM_URL}/session/{session_id}/element/{element_id}/value",
        json={"text": value}, timeout=5)

def get_text(session_id: str, element_id: str) -> str:
    r = requests.get(f"{APPIUM_URL}/session/{session_id}/element/{element_id}/text",
        timeout=5)
    return r.json().get("value", "")

def screenshot(session_id: str, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = requests.get(f"{APPIUM_URL}/session/{session_id}/screenshot", timeout=10)
    with open(path, "wb") as f:
        f.write(base64.b64decode(r.json().get("value", "")))
```

### helpers/ios/session.py — iOS Session Factory

```python
"""iOS-specific speed-optimized Appium session factory."""
import requests
from helpers.session import APPIUM_URL

WDA_URL = "http://127.0.0.1:8100"

def create_session(udid: str, bundle_id: str, no_reset: bool = True) -> str:
    """Create speed-optimized iOS/XCUITest session. Returns session ID."""
    caps = {"capabilities": {"alwaysMatch": {
        "platformName": "iOS",
        "appium:automationName": "XCUITest",
        "appium:udid": udid,
        "appium:bundleId": bundle_id,
        "appium:noReset": no_reset,
        "appium:newCommandTimeout": 300,
        "appium:webDriverAgentUrl": WDA_URL,
        "appium:usePrebuiltWDA": True,
        "appium:wdaLaunchTimeout": 30000,
        "appium:wdaConnectionTimeout": 30000,
        "appium:autoAcceptAlerts": True,    # dismiss system permission dialogs automatically
        "appium:implicitWaitTimeout": 5000,
    }}}
    r = requests.post(f"{APPIUM_URL}/session", json=caps, timeout=30)
    r.raise_for_status()
    return r.json()["value"]["sessionId"]
```

### helpers/ios/permissions.py — iOS Permission Safety Net

```python
"""iOS app-level permission dialog handler (safety net beyond autoAcceptAlerts)."""
from helpers.session import find, tap

# These are app-level dialogs not caught by autoAcceptAlerts
_BUTTONS = [
    ("accessibility id", "Allow"),
    ("accessibility id", "Allow While Using App"),
    ("accessibility id", "Allow Once"),
    ("accessibility id", "OK"),
    ("accessibility id", "Continue"),
    ("accessibility id", "Got It"),
    ("accessibility id", "Not Now"),
]

def dismiss_permissions(session_id: str) -> bool:
    """Tap the first visible permission button. Call after every navigation."""
    for strategy, selector in _BUTTONS:
        el = find(session_id, strategy, selector, timeout=1)
        if el:
            tap(session_id, el)
            return True
    return False
```

### helpers/android/session.py — Android Session Factory

```python
"""Android-specific speed-optimized Appium session factory."""
import requests
from helpers.session import APPIUM_URL

def create_session(udid: str, app_package: str, app_activity: str,
                   no_reset: bool = True) -> str:
    """Create speed-optimized Android/UIAutomator2 session. Returns session ID."""
    caps = {"capabilities": {"alwaysMatch": {
        "platformName": "Android",
        "appium:automationName": "UIAutomator2",
        "appium:udid": udid,
        "appium:appPackage": app_package,
        "appium:appActivity": app_activity,
        "appium:noReset": no_reset,
        "appium:newCommandTimeout": 300,
        "appium:autoGrantPermissions": True,  # grant ALL runtime permissions automatically
        "appium:implicitWaitTimeout": 5000,
        "appium:skipUnlock": True,
    }}}
    r = requests.post(f"{APPIUM_URL}/session", json=caps, timeout=30)
    r.raise_for_status()
    return r.json()["value"]["sessionId"]
```

### helpers/android/permissions.py — Android Permission Handler

```python
"""Android permission handler.
autoGrantPermissions: True in session caps handles runtime permissions automatically.
This module provides a dismiss_permissions() stub for interface compatibility with iOS code.
"""

def dismiss_permissions(session_id: str) -> bool:
    """No-op on Android — autoGrantPermissions handles all runtime permission dialogs."""
    return False
```

### helpers/login.py — Platform-Aware Login (Shared)

```python
"""Login flow shared across iOS and Android. Platform detected from XPath strategy."""
import time
from helpers.session import find, tap, set_value, get_text

def login(session_id: str, credentials: dict, platform: str = "ios"):
    """Fill login fields and submit. platform: 'ios' | 'android'"""
    time.sleep(1)
    field_xpath = (
        "//XCUIElementTypeTextField[contains(@placeholderValue,'{name}')]"
        if platform == "ios" else
        "//android.widget.EditText[contains(@hint,'{name}')]"
    )
    for field_name, value in credentials.items():
        el = (find(session_id, "accessibility id", field_name, timeout=4)
              or find(session_id, "xpath", field_xpath.format(name=field_name), timeout=3))
        if not el:
            continue
        tap(session_id, el)
        time.sleep(0.2)
        set_value(session_id, el, value)
        time.sleep(0.2)
        if get_text(session_id, el) != value:
            _type_via_keyboard(session_id, value, platform)
    # Submit
    btn = (find(session_id, "accessibility id", "Login", timeout=3)
           or find(session_id, "accessibility id", "Log In", timeout=2)
           or find(session_id, "xpath",
               "//XCUIElementTypeButton[contains(@name,'Login')]" if platform == "ios"
               else "//android.widget.Button[contains(@text,'Login')]", timeout=2))
    if btn:
        tap(session_id, btn)
    time.sleep(2)

def _type_via_keyboard(session_id: str, text: str, platform: str):
    from helpers.session import find, tap
    for char in text:
        key_xpath = (f"//XCUIElementTypeKey[@name='{char}']" if platform == "ios"
                     else f"//android.widget.Button[@content-desc='{char}']")
        key = find(session_id, "xpath", key_xpath, timeout=1)
        if key:
            tap(session_id, key)
```

### helpers/navigation.py — Platform-Aware Navigation (Shared)

```python
"""Common navigation helpers shared across iOS and Android."""
import time
from helpers.session import find, tap, APPIUM_URL
import requests

def go_to_tab(session_id: str, tab_name: str, platform: str = "ios"):
    """Tap a bottom tab bar item by accessibility name."""
    el = find(session_id, "accessibility id", tab_name, timeout=5)
    if el:
        tap(session_id, el)
        _dismiss(session_id, platform)
        time.sleep(0.8)

def go_back(session_id: str, platform: str = "ios"):
    """Navigate back: Back button on iOS, BACK key on Android."""
    if platform == "android":
        requests.post(f"{APPIUM_URL}/session/{session_id}/keys",
            json={"value": ["\ue002"]}, timeout=5)
    else:
        btn = find(session_id, "accessibility id", "Back", timeout=2)
        if btn:
            tap(session_id, btn)
    time.sleep(0.5)

def _dismiss(session_id: str, platform: str):
    if platform == "ios":
        from helpers.ios.permissions import dismiss_permissions
        dismiss_permissions(session_id)
    # Android: autoGrantPermissions handles it

# Add new navigation functions here as tickets require them
# e.g.: def go_to_reschedule(session_id, platform, job_index=0): ...
```

### ticket-tests-scripts/ios/<TICKET_ID>/test_<TICKET_ID>.py

```python
"""
Auto-generated test — <TICKET_ID>: <Ticket Title>
Platform  : iOS
Generated : <YYYY-MM-DD HH:MM>
Build     : v<version> (build <buildNumber>)
Device    : <deviceName> (<udid>)
Account   : <account label>

To rerun on a new build: update UDID / BUNDLE_ID below.
Run: python test_<TICKET_ID>.py
"""
import sys, os, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, ROOT)

from helpers.session import delete_all_sessions, find, tap, screenshot
from helpers.ios.session import create_session
from helpers.ios.permissions import dismiss_permissions
from helpers.login import login
from helpers.navigation import go_to_tab, go_back

UDID      = "<udid>"
BUNDLE_ID = "<bundleId>"
PLATFORM  = "ios"
CREDS     = <credentials_dict>
SHOTS     = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SHOTS, exist_ok=True)

RESULTS = {}

def assert_visible(S, strategy, selector, label, timeout=5):
    el = find(S, strategy, selector, timeout=timeout)
    if el:
        print(f"  ✅ {label}")
        RESULTS[label] = "PASS"
    else:
        print(f"  ❌ {label} — not found: {selector}")
        screenshot(S, f"{SHOTS}/{label.replace(' ','_')}.png")
        RESULTS[label] = "FAIL"
    return el

def assert_hidden(S, strategy, selector, label):
    el = find(S, strategy, selector, timeout=2)
    if not el:
        print(f"  ✅ {label} — correctly hidden")
        RESULTS[label] = "PASS"
    else:
        print(f"  ❌ {label} — should be hidden but visible: {selector}")
        screenshot(S, f"{SHOTS}/{label.replace(' ','_')}.png")
        RESULTS[label] = "FAIL"

def main():
    print(f"Test: <TICKET_ID> — <Ticket Title> [iOS]")
    delete_all_sessions()
    S = create_session(UDID, BUNDLE_ID)
    dismiss_permissions(S)
    time.sleep(0.5)
    login(S, CREDS, platform=PLATFORM)
    dismiss_permissions(S)
    time.sleep(0.5)

    # ── AC steps — filled from actual Appium interactions ─────────────────────
    # <GENERATED_AC_STEPS_HERE>

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n── Results ──────────────────────────────────")
    for label, result in RESULTS.items():
        icon = "✅" if result == "PASS" else "❌"
        print(f"  {icon} {label}: {result}")
    passed = sum(1 for v in RESULTS.values() if v == "PASS")
    print(f"\n{passed}/{len(RESULTS)} ACs passed")

if __name__ == "__main__":
    main()
```

### ticket-tests-scripts/android/<TICKET_ID>/test_<TICKET_ID>.py

Same structure as iOS version. Differences:
- Import `from helpers.android.session import create_session`
- Import `from helpers.android.permissions import dismiss_permissions`
- `PLATFORM = "android"`
- `create_session(UDID, APP_PACKAGE, APP_ACTIVITY)`

### conftest.py (same for both platforms — platform flag differs)

```python
"""pytest fixtures for <TICKET_ID> — <platform>."""
import pytest, sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, ROOT)

from helpers.session import delete_all_sessions
# iOS:
from helpers.ios.session import create_session
# Android: from helpers.android.session import create_session

UDID      = "<udid>"
BUNDLE_ID = "<bundleId>"   # iOS only
PLATFORM  = "ios"

@pytest.fixture(scope="module")
def session():
    delete_all_sessions()
    sid = create_session(UDID, BUNDLE_ID)
    yield sid

@pytest.fixture
def creds():
    return <credentials_dict>
```

## Step 6 — Save Test Results

Write (or prepend to) `$OUTPUT_DIR/<project>/reports/<TICKET_ID>.md`.

If the file already exists → **prepend** the new entry at the top (most recent first).
If the file does not exist → create it.

```markdown
---
## [<TICKET_ID>] <Ticket Title>
**Date/Time:** <YYYY-MM-DD HH:MM:SS>
**Device:** <deviceName> (<udid>) — <platform> <osVersion>
**Account:** <account label>
**Build:** v<version> (build <buildNumber>)

### Acceptance Criteria Results

| # | AC | Result | Notes |
|---|-----|--------|-------|
| 1 | <AC text> | ✅ PASS / ❌ FAIL / ⚠️ BLOCKED | <detail> |

### Notes
<observations>

---
```

## Step 6b — Save Reusable Workflow

Create `$OUTPUT_DIR/<project>/test-ticket-driven/` if it doesn't exist.
Write `$OUTPUT_DIR/<project>/test-ticket-driven/<TICKET_ID>.md`.

Rules:
- Derive each step from actual Appium interactions performed during the test
- Write human-readable actions, not code
- FAIL/BLOCKED steps: include step + `> ⚠️ Known issue: <detail>`
- File already exists → overwrite

## Step 7 — Regression Offer

```
Ticket test complete. Results:
  ✅ AC #1 PASS
  ❌ AC #3 FAIL — screenshot saved

Do you want to run a full regression to check for side effects? (yes/no)
```

If yes → use `regression` skill.
Then → use `qa-report` skill.

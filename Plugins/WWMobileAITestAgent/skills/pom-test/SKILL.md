---
name: pom-test
description: Generate Page Object Model test files for every screen in navigation_map.json using pytest + appium-python-client. Output to $OUTPUT_DIR/<project>/test-pom-generated/.
---
> **Output directory:** Read `OUTPUT_DIR` from session memory (set by session-wizard Step 0). Use `$OUTPUT_DIR/<project>/` for all file paths instead of `projects/<project>/`.


# POM Auto-Generation

## Pre-flight

Load `$OUTPUT_DIR/<project>/nav_maps/navigation_map.json`. If it doesn't exist:
```
No navigation map found. Please run screen discovery first:
  [1] Automated Screen Discovery (from running app)
  [2] Codebase Screen Discovery (from repository)
```

## Output Folders

Primary POM output (pytest structure):
```
$OUTPUT_DIR/<project>/test-pom-generated/
```

Reusable standalone scripts (imports shared helpers):
```
$OUTPUT_DIR/<project>/auto-generated-scripts/pom-test-scripts/
├── ios/
│   ├── run_smoke.py
│   ├── run_all.py
│   └── screens/<screen>.py
└── android/
    ├── run_smoke.py
    ├── run_all.py
    └── screens/<screen>.py
```

## File Structure Generated (test-pom-generated/)

```
test-pom-generated/
├── README.md
├── requirements.txt
├── conftest.py              ← speed-optimized session fixtures
├── pages/
│   ├── base_page.py         ← BasePage with 5s timeout + permission handler
│   ├── login_page.py
│   ├── home_page.py
│   └── <screen>_page.py     ← one per screen in nav map
└── tests/
    ├── test_smoke.py
    ├── test_login.py
    └── test_<screen>.py     ← one per screen
```

## conftest.py — Speed-Optimized

```python
import pytest
from appium import webdriver
from appium.options.ios.xcuitest.base import XCUITestOptions
from appium.options.android.uiautomator2.base import UiAutomator2Options

def pytest_addoption(parser):
    parser.addoption("--platform", default="ios", choices=["android", "ios"])
    parser.addoption("--device-udid", required=True)
    parser.addoption("--app-path", default=None)
    parser.addoption("--bundle-id", default="<bundleId>")

@pytest.fixture(scope="session")
def driver(request):
    platform = request.config.getoption("--platform")
    udid     = request.config.getoption("--device-udid")

    if platform == "android":
        options = UiAutomator2Options()
        options.udid = udid
        options.no_reset = True
        options.new_command_timeout = 300
        options.set_capability("appium:autoGrantPermissions", True)
        options.set_capability("appium:skipUnlock", True)
        options.set_capability("appium:implicitWaitTimeout", 5000)
        app_path = request.config.getoption("--app-path")
        if app_path:
            options.app = app_path
    else:
        options = XCUITestOptions()
        options.udid = udid
        options.no_reset = True
        options.new_command_timeout = 300
        options.bundle_id = request.config.getoption("--bundle-id")
        options.set_capability("appium:webDriverAgentUrl", "http://127.0.0.1:8100")
        options.set_capability("appium:usePrebuiltWDA", True)
        options.set_capability("appium:wdaLaunchTimeout", 30000)
        options.set_capability("appium:wdaConnectionTimeout", 30000)
        options.set_capability("appium:autoAcceptAlerts", True)
        options.set_capability("appium:implicitWaitTimeout", 5000)

    d = webdriver.Remote("http://127.0.0.1:4723", options=options)
    d.implicitly_wait(5)
    yield d
    d.quit()

@pytest.fixture
def credentials():
    return <credentials_dict>
```

## base_page.py — Speed-Optimized

```python
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    TIMEOUT = 5   # reduced from stepTimeoutMs for faster failures

    _PERMISSION_BUTTONS = [
        "Allow", "Allow While Using App", "Allow Once",
        "OK", "Continue", "Got It", "Not Now",
    ]

    def __init__(self, driver):
        self.driver = driver

    def find(self, accessibility_id=None, resource_id=None, xpath=None, timeout=None):
        """Locator priority: AccessibilityId > resource-id > XPath"""
        wait = WebDriverWait(self.driver, timeout or self.TIMEOUT)
        if accessibility_id:
            return wait.until(EC.presence_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID, accessibility_id)))
        if resource_id:
            return wait.until(EC.presence_of_element_located(
                (AppiumBy.ID, resource_id)))
        return wait.until(EC.presence_of_element_located(
            (AppiumBy.XPATH, xpath)))

    def find_safe(self, timeout=2, **kwargs):
        try:
            return self.find(**kwargs, timeout=timeout)
        except Exception:
            return None

    def tap(self, **kwargs):
        self.find(**kwargs).click()
        self.dismiss_permissions()

    def type_text(self, text, **kwargs):
        el = self.find(**kwargs)
        el.clear()
        el.send_keys(text)

    def get_text(self, **kwargs):
        return self.find(**kwargs).text

    def is_visible(self, timeout=2, **kwargs):
        el = self.find_safe(timeout=timeout, **kwargs)
        return el is not None and el.is_displayed()

    def screenshot(self, name):
        import os; os.makedirs("screenshots", exist_ok=True)
        self.driver.save_screenshot(f"screenshots/{name}.png")

    def dismiss_permissions(self):
        """Safety net for app-level dialogs (autoAcceptAlerts handles system alerts)."""
        for btn in self._PERMISSION_BUTTONS:
            el = self.find_safe(accessibility_id=btn, timeout=1)
            if el:
                try: el.click(); return True
                except Exception: pass
        return False
```

## Per-Screen Page Object Pattern

For each screen in `navigation_map.json`:

```python
# pages/<screen_snake_case>_page.py
from .base_page import BasePage

class <ScreenName>Page(BasePage):
    """
    Screen: <route>
    Path  : <navigation path>
    Prereq: <prerequisites>
    """
    BTN_<ELEMENT> = {"accessibility_id": "<AutomationId>"}
    LBL_<ELEMENT> = {"accessibility_id": "<AutomationId>"}

    def navigate_to(self):
        """Navigate from home: <path>"""
        pass

    def assert_visible(self):
        assert self.is_visible(**self.LBL_<TITLE>), "<ScreenName> did not load"
```

## Per-Screen Test Pattern

```python
# tests/test_<screen>.py
import pytest
from pages.<screen>_page import <Screen>Page
from pages.login_page import LoginPage

class Test<Screen>:
    def test_screen_loads(self, driver, credentials):
        LoginPage(driver).login(credentials)
        page = <Screen>Page(driver)
        page.navigate_to()
        page.assert_visible()
```

## Generation Process

For EACH screen in the navigation map:
1. Generate `pages/<screen>_page.py` with locators and navigation
2. Generate `tests/test_<screen>.py` with smoke + one test per interactive element
3. Locator priority: `accessibility_id` → `resource_id` (bundle prefix) → commented XPath

After all POM files:
- Write `requirements.txt` (`appium-python-client>=3.1.0`, `pytest>=7.4.0`, `selenium>=4.15.0`)
- Write `README.md`

## Autoscripts Generation

After POM generation, also generate scripts in
`$OUTPUT_DIR/<project>/auto-generated-scripts/pom-test-scripts/`.

Ensure `auto-generated-scripts/helpers/` exists with shared files
(`session.py`, `login.py`, `navigation.py`, `ios/session.py`, `ios/permissions.py`,
`android/session.py`, `android/permissions.py`). Create if missing, never overwrite existing.

Generate for BOTH platforms if nav map was built from both, otherwise only for the current platform.

### pom-test-scripts/ios/run_smoke.py

```python
"""
POM Smoke runner — iOS.
Visits every main tab, asserts it loads. Rerun on any build: update UDID/BUNDLE_ID.
Run: python run_smoke.py
"""
import sys, os, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, ROOT)

from helpers.session import delete_all_sessions, find, screenshot
from helpers.ios.session import create_session
from helpers.ios.permissions import dismiss_permissions
from helpers.login import login
from helpers.navigation import go_to_tab

UDID      = "<udid>"
BUNDLE_ID = "<bundleId>"
PLATFORM  = "ios"
CREDS     = <credentials_dict>
TABS      = <tab_bar_items_from_nav_map>
SHOTS     = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SHOTS, exist_ok=True)

RESULTS = {}

def main():
    delete_all_sessions()
    S = create_session(UDID, BUNDLE_ID)
    dismiss_permissions(S); time.sleep(0.5)
    login(S, CREDS, platform=PLATFORM)
    dismiss_permissions(S); time.sleep(0.5)

    for tab in TABS:
        go_to_tab(S, tab, platform=PLATFORM)
        time.sleep(0.8)
        el = find(S, "class name", "XCUIElementTypeWindow", timeout=3)
        if el:
            screenshot(S, f"{SHOTS}/smoke_{tab.replace(' ','_')}.png")
            print(f"  ✅ {tab}")
            RESULTS[tab] = "PASS"
        else:
            print(f"  ❌ {tab}")
            RESULTS[tab] = "FAIL"

    passed = sum(1 for v in RESULTS.values() if v == "PASS")
    print(f"\nSmoke iOS: {passed}/{len(RESULTS)} tabs passed")

if __name__ == "__main__":
    main()
```

### pom-test-scripts/android/run_smoke.py

Same structure. Differences:
- `from helpers.android.session import create_session`
- `from helpers.android.permissions import dismiss_permissions`
- `PLATFORM = "android"`
- `create_session(UDID, APP_PACKAGE, APP_ACTIVITY)`
- Tab assertion: `find(S, "class name", "android.view.ViewGroup", timeout=3)`

### pom-test-scripts/ios/screens/<screen>.py (one per screen)

```python
"""
Screen: <ScreenName> — iOS
Path  : <navigation path>
Run   : python <screen>.py
"""
import sys, os, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
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
SHOTS     = os.path.join(os.path.dirname(__file__), "..", "screenshots")
os.makedirs(SHOTS, exist_ok=True)

def test_<screen_snake>(S):
    <navigation_steps>
    el = find(S, "accessibility id", "<title_element>", timeout=5)
    assert el, "<ScreenName> did not load"
    screenshot(S, f"{SHOTS}/<screen_snake>_loaded.png")
    print("  ✅ <ScreenName> loaded")
    <element_assertions>

if __name__ == "__main__":
    delete_all_sessions()
    S = create_session(UDID, BUNDLE_ID)
    dismiss_permissions(S)
    login(S, CREDS, platform=PLATFORM)
    test_<screen_snake>(S)
```

Display after generation:
```
✅ POM generation complete
   Pages generated           : N
   Tests generated           : N
   Autoscripts iOS            : N screens + run_smoke.py + run_all.py
   Autoscripts Android        : N screens + run_smoke.py + run_all.py
   Primary output             : $OUTPUT_DIR/<project>/test-pom-generated/
   Autoscripts iOS            : $OUTPUT_DIR/<project>/auto-generated-scripts/pom-test-scripts/ios/
   Autoscripts Android        : $OUTPUT_DIR/<project>/auto-generated-scripts/pom-test-scripts/android/

Run POM tests (iOS):
  cd "$OUTPUT_DIR/<project>/test-pom-generated"
  pytest tests/ --platform ios --device-udid <udid> --bundle-id <bundleId> -v

Run autoscripts smoke (iOS):
  python "$OUTPUT_DIR/<project>/auto-generated-scripts/pom-test-scripts/ios/run_smoke.py"
```

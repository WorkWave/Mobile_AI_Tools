---
name: session-wizard
description: "Full session startup wizard for WWMobileAITestAgent. Guides the user through output directory setup, environment check, Firebase setup, project selection, OS, device, build source, app install, authentication, navigation map, and testing mode."
---

# Session Startup Wizard

Run each step in order. Persist all selections in session memory for use by subsequent skills and commands.

---

## Step 0 — Output Directory

All generated data (builds, credentials, navigation maps, reports, generated tests) is saved outside the plugin folder to keep the plugin clean and portable.

### Read saved directory

Check if `outputdirectory.txt` exists in the installed plugin folder.

**If `outputdirectory.txt` exists**, read the saved path and show:
```
Output directory:

  [1] Use current saved: <saved_path>
  [2] Move to a different directory
  [3] Start fresh with a new directory (old data stays, just changes the pointer)
```
- If [1] → use the saved path, continue to Step 1
- If [2] or [3] → ask: "Enter the base folder path (WWMobileTestAgentAIResults will be created inside it):"
  - Resolve `~` or `%USERPROFILE%` to absolute path
  - **Immediately** write the resolved path to `outputdirectory.txt` in the plugin folder
  - Store `OUTPUT_DIR` in session memory

**If `outputdirectory.txt` does NOT exist**, detect the OS default and show:
```
Where do you want to save test outputs?

  [1] Use default: <default_path>
  [2] Change directory — enter a custom base path
```
- macOS/Linux default: `~/WWMobileTestAgentAIResults` (resolved to absolute)
- Windows default: `%USERPROFILE%\WWMobileTestAgentAIResults` (resolved to absolute)
- If [1] → use the default path
- If [2] → ask: "Enter the base folder path (WWMobileTestAgentAIResults will be created inside it):"
  - Resolve `~` or `%USERPROFILE%` to absolute path
- **Immediately** write the resolved path to `outputdirectory.txt` in the plugin folder
- Store `OUTPUT_DIR` in session memory

### Create directory structure

After writing `outputdirectory.txt`, create the following structure if it doesn't exist:
```
<OUTPUT_DIR>/
  PestPac/
    builds/
    credentials/
    reports/
    nav_maps/
    test-pom-generated/
    test-manual-workflow/
    test-ticket-driven/
  RealGreen/
    builds/
    credentials/
    reports/
    nav_maps/
    test-pom-generated/
    test-manual-workflow/
    test-ticket-driven/
  WinTeam/
    builds/
    credentials/
    reports/
    nav_maps/
    test-pom-generated/
    test-manual-workflow/
    test-ticket-driven/
  RouteManager/
    builds/
    credentials/
    reports/
    nav_maps/
    test-pom-generated/
    test-manual-workflow/
    test-ticket-driven/
```

Store `OUTPUT_DIR: <absolute_path>` in session memory.

Show: `✅ Output directory: <OUTPUT_DIR>`

---

## Step 1 — Environment Verification

Use the `verify-environment` skill.
If result is NOT READY → stop and ask the user to resolve missing tools.
If READY WITH WARNINGS → continue but note the warnings.

---

## Step 2 — Firebase Keys

Use the `setup-firebase` skill. It will automatically load from `firebase_keys.json` if already configured (no folder prompt needed), or guide the user through the initial setup. It also pre-populates `$OUTPUT_DIR/<project>/config.json` for each matched project.

---

## Step 3 — Select Project

```
Which project do you want to test?

  [1] PestPac
  [2] RealGreen
  [3] WinTeam
  [4] RouteManager
```

After the user picks a project, check if `$OUTPUT_DIR/<selected>/config.json` exists:

### If config.json EXISTS → load and show:
```
Project config loaded:
  Name       : RealGreen
  Repository : WorkWave/Real-Green-Mobile
  Local repo : /Users/you/Workspace/MobilePrj/Real-Green-Mobile
  Firebase   : realgreen-e72e9
  Bundle ID  : com.workwave.realgreen (android) / com.workwave.realgreen (ios)

  [1] Use this config
  [2] Reconfigure
```
- If [1] → store in session, continue to Step 4
- If [2] → run the config setup procedure below

### If config.json DOES NOT EXIST → run config setup:

> **Note:** If `setup-firebase` ran in Step 2, it already created `config.json` with all known defaults and Firebase data pre-filled. In that case, this branch is unlikely to be reached — but follow this procedure if it wasn't created.

Pre-populate the following known defaults per project:

| Field | PestPac | RealGreen | WinTeam | RouteManager |
|---|---|---|---|---|
| repository | WorkWave/PestPac-Mobile | WorkWave/Real-Green-Mobile | WorkWave/WinTeam-Mobile | WorkWave/RouteManager-Mobile |
| defaultBranch | dev | dev | dev | dev |
| bundleId.android | com.workwave.pestpac | com.workwave.realgreen | com.workwave.winteam | com.workwave.routemanager |
| bundleId.ios | com.workwave.pestpac | com.workwave.realgreen | com.workwave.winteam | com.workwave.routemanager |
| authSchema | sso (email+password) | custom (companyNumber+employeeId+password) | sso (email+password) | standard (email+password) |
| stepTimeoutMs | 10000 | 10000 | 10000 | 10000 |

Ask the user only for the fields that require local knowledge:

```
Configure <Project>:

  Local repo path (leave blank to skip):
  Default: ~/Workspace/MobilePrj/<Project>-Mobile
  >
```

For `firebaseProject` and `firebaseServiceAccountPath`: read from the Firebase session mapping set in Step 2.
- If matched → auto-fill from session (already extracted by `setup-firebase`)
- If `firebaseAppId` is empty → leave empty and note: "Firebase App IDs can be added later via /getFirebaseBuilds"

Show the assembled config for confirmation:
```
Config for <Project>:
  Repository  : WorkWave/<Project>-Mobile
  Local repo  : <path>
  Firebase    : <project_id or "not set">
  Bundle ID   : <android> / <ios>
  Auth        : <type> (<fields>)

Save this config? (yes/no)
```

On yes → write to `$OUTPUT_DIR/<selected>/config.json` and store in session.

---

## Step 4 — Select OS

```
Target platform?

  [1] Android
  [2] iOS
```

Store `platform: android | ios` in session.

---

## Step 5 — Select Device

- If Android → run `/getAndroidDeviceAndSimulator` and show the list
- If iOS → run `/getIosDeviceAndSimulator` and show the list

```
Select a device by number:
```

Store selected device (`udid`, `name`, `type`, `osVersion`) in session.

If the selected device is an iOS simulator that is **Shutdown**:
```bash
xcrun simctl boot <udid>
```
Wait for it to boot before continuing.

---

## Step 6 — Select Build

```
Which build do you want to install?

  [1] Local file (provide path to .apk / .ipa)
  [2] Firebase App Distribution
  [3] Use currently installed build on device
```

**If Local:**
```
Enter the absolute path to the .apk or .ipa file:
```
Validate the file exists. Store `buildSource: local`, `buildPath: <path>`.

**If Firebase:**
Run `/getFirebaseBuilds <project> <os>`.
User selects a build (1-11).
Store `buildSource: firebase`, `buildInfo: { version, buildNumber, downloadUrl }`.

**If Currently Installed:**
Detect the installed version on the selected device:

- iOS Physical:
```bash
ideviceinstaller -u <udid> -l 2>/dev/null | grep <bundleId>
```
If `ideviceinstaller` is not available, fall back to:
```bash
ios-deploy --list-3rd-party-apps 2>/dev/null | grep <bundleId>
```
If neither works, skip version detection and show: "Version detection not available — proceeding with installed build."

- iOS Simulator:
```bash
xcrun simctl listapps <udid> 2>/dev/null | python3 -c "
import sys, plistlib
data = plistlib.loads(sys.stdin.buffer.read())
bundle = '<bundleId>'
if bundle in data:
    app = data[bundle]
    print(app.get('CFBundleShortVersionString','?'), app.get('CFBundleVersion','?'))
"
```

- Android:
```bash
adb -s <udid> shell dumpsys package <bundleId> 2>/dev/null | grep -E "versionName|versionCode"
```

Show the detected version (or "unknown" if detection failed). Store `buildSource: installed`, `buildVersion: <detected or "unknown">`.
Skip Step 7 (no download or install needed). Appium session will use `bundleId` capability instead of `app`.

---

## Step 7 — Deploy Build

> **Skip this step entirely if `buildSource: installed`** (user selected option [3] in Step 6). Proceed directly to Step 8.

Download destination: `$OUTPUT_DIR/<project>/builds/`

Check if the build file already exists in `$OUTPUT_DIR/<project>/builds/` before downloading.

**Firebase download (if not already present):**
Use the Firebase App Distribution REST API (service account auth) to download the binary to `$OUTPUT_DIR/<project>/builds/<project>-<os>-<buildNumber>.ipa|apk`.

**Install on device:**

Android (physical or emulator):
```bash
adb -s <udid> install -r <apkPath>
```

iOS Simulator:
```bash
xcrun simctl install <udid> <ipaPath>
```

iOS Physical:

Installation is handled via Appium XCUITest driver — no `ios-deploy` needed. The app is installed automatically when the Appium session is created with the `app` capability.

Before creating the session, check if a WorkWave provisioning profile is installed on the machine:
```bash
ls ~/Library/MobileDevice/Provisioning\ Profiles/*.mobileprovision 2>/dev/null
```
For each `.mobileprovision` file found, extract `TeamName`, `TeamIdentifier`, and profile type:
```bash
security cms -D -i <file.mobileprovision> | grep -A1 "TeamName\|TeamIdentifier\|ProvisionalProfileType\|get-task-allow"
```

**Profile selection priority for physical devices:**
1. Prefer a WorkWave **Ad Hoc** profile — standard for physical test devices
2. Fall back to any other WorkWave profile if Ad Hoc is not found
3. If no WorkWave profile exists, proceed without specifying one

Pass the selected profile via Appium capabilities when creating the session. Use **only** `xcodeOrgId` — do NOT set `xcodeSigningId` or `CODE_SIGN_IDENTITY`, as they conflict with the app's existing automatic signing configuration.

**If `buildSource: installed`** — use `bundleId` instead of `app` (the app is already on device, no install needed):
```json
{
  "platformName": "iOS",
  "appium:udid": "<udid>",
  "appium:bundleId": "<bundleId>",
  "appium:xcodeOrgId": "8V5NXR3J7H"
}
```

**If `buildSource: local` or `buildSource: firebase`** — use `app` to install:
```json
{
  "platformName": "iOS",
  "appium:udid": "<udid>",
  "appium:app": "<ipaPath>",
  "appium:xcodeOrgId": "8V5NXR3J7H"
}
```

- `xcodeOrgId` is always `8V5NXR3J7H` (WorkWave team ID)
- If an Ad Hoc profile was found, also add `appium:provisioningProfileId: "<profileUUID>"`
- Never set `xcodeSigningId` — it overrides `CODE_SIGN_IDENTITY` and breaks automatic signing

If no WorkWave profile is found, omit `provisioningProfileId` but keep `xcodeOrgId`.

Show progress. On success: "✅ Build installed on <deviceName>"
On failure: show the error and ask if the user wants to retry or pick a different build.

---

## Step 8 — Authentication

Load `authSchema` from `$OUTPUT_DIR/<project>/config.json` (already in session from Step 3).

Check if saved credentials exist in `$OUTPUT_DIR/<project>/credentials/credentials.json`.
If yes:
```
Saved accounts for <Project>:
  [1] Frank (frank@workwave.com)
  [2] Test QA (qa@workwave.com)
  [3] Add new account

Select account (1-3):
```

If no saved credentials:
Prompt for each field defined in `authSchema.fields`:
```
<label>: [input]
```
Ask: "Save these credentials for future sessions? (yes/no)"
If yes → save to `$OUTPUT_DIR/<project>/credentials/credentials.json`.

Store selected credentials in session.

---

## Step 9 — Navigation Map

```
How do you want to build the navigation map?

  [1] Automated Screen Discovery  — explore the running app via Appium (after login)
  [2] Codebase Screen Discovery   — analyze the repository source code
  [3] Skip                        — use existing navigation_map.json if available
```

**If [1]** → use `automated-screen-discovery` skill
**If [2]** → use `codebase-screen-discovery` skill
**If [3]** → check if `$OUTPUT_DIR/<project>/nav_maps/navigation_map.json` exists
  - If yes → load it silently
  - If no → warn: "No navigation map found. Some test features will be limited. Consider running discovery later."

---

## Step 10 — Test Mode

```
Select testing mode:

  [1] Ticket-Driven Test      — test a specific Jira ticket's acceptance criteria
  [2] POM Auto-Generation     — generate Page Object Model tests for all screens
  [3] Workflow Test         — run a structured test workflow from a markdown file
```

**If [1]** → use `ticket-test` skill
**If [2]** → use `pom-test` skill
**If [3]** → use `workflow-test` skill

---

## Session Summary

Before launching the selected test mode, show:

```
══════════════════════════════════════════════
  Session Ready
══════════════════════════════════════════════
  Project    : RealGreen
  Platform   : iOS
  Device     : Francesco's iPhone (iOS 26.3.1)
  Build      : v99.9.11059 (build 11059) from Firebase
  Account    : Saffioti (company: 848547)
  Nav Map    : 127 screens (last analyzed: 2026-03-21)
  Output Dir : ~/WWMobileTestAgentAIResults
  Mode       : Ticket-Driven Test
══════════════════════════════════════════════
```

Then proceed to the selected testing mode.

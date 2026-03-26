---
name: regression-test
description: "Run a full regression suite — smoke pass, navigation regression across all screens, and crash monitoring via device logs. Follows QA best practices."
---
> **Session data:** Read `OUTPUT_DIR`, `project`, `platform`, `udid`, and `config` from session memory (set by session-wizard). If any value is missing → load from `$OUTPUT_DIR/<project>/config.json` directly before proceeding.


# Regression Testing

## Goal

Verify the app does not crash and all core navigation paths remain stable. This is NOT functional testing — it validates stability and navigation integrity.

## Step 1 — Start Crash Monitor (Background)

**Android:** Start monitoring in background:
```bash
adb -s <udid> logcat -c && adb -s <udid> logcat *:E > /tmp/regression_logcat.txt &
LOGCAT_PID=$!
```
Watch for: `FATAL EXCEPTION`, `ANR in`, `force closed`, `signal 6`, `SIGSEGV`

**iOS:**
```bash
xcrun simctl spawn <udid> log stream --level error > /tmp/regression_ios.txt &
IOS_LOG_PID=$!
```
Watch for: `EXC_BAD_ACCESS`, `signal 6`, `abort()`, `Terminating app due to uncaught exception`

## Step 2 — Smoke Pass

1. Force-stop the app: `adb -s <udid> shell am force-stop <bundleId>` or `xcrun simctl terminate <udid> <bundleId>`
2. Launch the app fresh
3. Complete login with session credentials
4. Assert home screen loads within 15 seconds

Result: PASS / FAIL
If FAIL → stop regression and report: "App failed to launch or login. Regression aborted."

## Step 3 — Navigation Regression

Read `platform` from session memory. Load all screens from `navigation_map_<platform>.json`. For each screen:

1. Navigate to the screen following its recorded path
2. Assert the screen loaded:
   - Page source is non-empty
   - No error dialog / crash dialog visible
   - No "App has stopped" / "Unfortunately..." system dialog (Android)
3. Screenshot the screen — always use `maxWidth: 150` (full HTML viewer is ~10k tokens)
4. Check crash log for new entries since last check
5. Navigate back to home (use back stack or tap Home tab)
6. Wait 500ms between screens

Track:
- ✅ PASS — screen loaded normally
- ❌ FAIL — screen did not load, error shown, or navigation stuck
- 💥 CRASH — crash entry detected in device log

## Step 4 — State Regression

After navigating all screens:
1. Rotate device to landscape → check no crash → rotate back
2. Background the app (press Home) → wait 3s → foreground it → check no crash
3. Trigger a network interruption if possible (airplane mode 2s → off) → check app recovers

## Step 5 — Stop Crash Monitor

```bash
kill $LOGCAT_PID 2>/dev/null
kill $IOS_LOG_PID 2>/dev/null
```

Parse crash log files for any entries captured during the run.

## Step 6 — Report

Compile regression results and pass to `qa-report` skill:

```
Regression Summary
══════════════════════════════════════
  Screens tested  : 127
  ✅ Passed       : 124
  ❌ Failed       : 2   (ScheduleView, NewJobModal)
  💥 Crashes      : 1   (crash on navigate to ReportScreen)
  ⏱  Duration     : 8m 34s
══════════════════════════════════════
```

For each FAIL or CRASH, include:
- Screen name and navigation path
- Screenshot file
- Relevant crash log excerpt (last 20 lines before crash)
- QA Lead recommendation (e.g. "ReportScreen crashes on cold launch — likely uninitialized data dependency")

---
name: codebase-screen-discovery
description: Analyze the .NET Xamarin/MAUI mobile repository (always on dev branch) to map navigation structure, screens, routes, and ViewModels. Saves to codebase_navigation_map.json, then merges into navigation_map.json. Skips if the git commit hash hasn't changed since last analysis.
---

> **Session data:** Read `OUTPUT_DIR`, `project`, `platform`, `udid`, and `config` from session memory (set by session-wizard). If any value is missing → load from `$OUTPUT_DIR/<project>/config.json` directly before proceeding.

# Codebase Screen Discovery

## Pre-flight Check

1. Load `localRepoPath` from `$OUTPUT_DIR/<project>/config.json` (already in session)
2. Ask: "Is the repository already cloned locally? If not, I'll clone it."
   - If not cloned: `git clone git@github.com:<repository>.git <localRepoPath>`
3. Checkout dev branch: `git -C <localRepoPath> checkout dev && git -C <localRepoPath> pull`
4. Get current commit hash: `git -C <localRepoPath> rev-parse HEAD`
5. Check existing `$OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map.json`:
   - If exists and `last_commit_hash` matches current → say "Codebase nav map is up to date (commit: <hash>). Skipping analysis." and exit.
   - If exists but hash differs → say "Repository has changed since last analysis. Updating codebase nav map..."
   - If not exists → proceed with full analysis

## Step 1 — Dispatch Repository Analysis Subagent

Use the Agent tool to dispatch a subagent with this task:

> Analyze the .NET mobile repository at `<localRepoPath>` on branch `dev`.
> Detect the navigation architecture and map all screens/routes.
>
> **What to look for:**
>
> 1. Navigation enum files (search for `NavigationRouts`, `AppRoute`, `Routes`, `PageKeys`)
> 2. Navigation service files (`NavigationService`, `INavigationService`, `AppNavigator`)
> 3. ViewModels that call navigation (search for `NavigateTo`, `PushAsync`, `GoToAsync`)
> 4. Android: Fragment transactions, NavGraph XML files (`res/navigation/`)
> 5. iOS: AppCoordinator, Storyboard segues, `pushViewController`, `present(`
> 6. MAUI Shell: `Shell.Current.GoToAsync`, `AppShell.xaml` routes
>
> **For each screen found, record:**
> - Route name / enum value
> - ViewModel class name and file path
> - View/Page class name and file path
> - Parent screen (what navigates to it)
> - Tab group (if inside a tab bar)
> - Required prerequisites (login, specific data, permissions)
> - Key interactive elements (from XAML: Buttons, Labels, Entries with AutomationId)
> - Navigation path from app launch
>
> Return the result as a JSON object matching the navigation_map.json schema.

## Step 2 — Save to codebase_navigation_map.json

Write the subagent's result to `$OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map.json`:

```json
{
  "project": "<project>",
  "repository": "<org/repo>",
  "branch": "dev",
  "last_commit_hash": "<sha>",
  "last_analyzed": "<ISO date>",
  "discovery_method": "codebase",
  "architecture": {
    "pattern": "MVVM",
    "core_framework": "Xamarin.Forms | MAUI",
    "navigation_abstraction": "NavigationService",
    "android_navigation": "Fragments | NavGraph",
    "ios_navigation": "AppCoordinator | Storyboard"
  },
  "authentication": {
    "type": "custom | sso | standard",
    "fields": ["companyNumber", "employeeId", "password"],
    "viewmodel": "LoginViewModel",
    "endpoint": "/account/login"
  },
  "entry_flow": {
    "android": { "launcher": "MainActivity", "flow": ["SplashActivity", "LoginPage", "HomePage"] },
    "ios":     { "launcher": "AppDelegate",  "flow": ["SplashView", "LoginPage", "HomePage"] }
  },
  "screens": {
    "Home": {},
    "Scheduling": {}
  },
  "key_files": {
    "navigation_enum": "src/Core/Navigation/NavigationRouts.cs",
    "navigation_service": "src/Core/Services/NavigationService.cs"
  }
}
```

## Step 3 — Merge into navigation_map.json

Check what exists in `$OUTPUT_DIR/<project>/nav_maps/`:

**If `appium_navigation_map.json` also exists → merge both:**

Merge strategy:
- Start from `codebase_navigation_map.json` as base (richer structure: routes, ViewModels, architecture)
- For each screen in `appium_navigation_map.json`:
  - If screen exists in codebase map → enrich `interactive_elements` with appium findings, keep codebase `path`/`route`/`viewmodel`
  - If screen exists only in appium → add it to the merged map with a note `"source": "appium_only"`
- For screens only in codebase → keep as-is with `"source": "codebase_only"`
- Set `"discovery_method": "merged"`, `"last_analyzed": <now>`, `"total_screens": <combined count>`

**If only `codebase_navigation_map.json` exists (no appium map):**

Copy it as-is to `navigation_map.json`.

**Write result to `$OUTPUT_DIR/<project>/nav_maps/navigation_map.json`.**

Report:
```
✅ Codebase analysis complete
   Screens found      : 127
   Architecture       : MVVM + NavigationService
   Codebase map saved : $OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map.json
   Nav map updated    : $OUTPUT_DIR/<project>/nav_maps/navigation_map.json  (merged | copied)
   Commit hash        : abc123...
```

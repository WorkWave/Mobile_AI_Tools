---
name: codebase-screen-discovery
description: Analyze the mobile repository to map navigation structure, screens, and routes. Detects architecture automatically (native, MVVM, or mixed). Dispatches a shared MVVM subagent only if MVVM layer is found, then dispatches platform subagents for Android and iOS. Saves to codebase_navigation_map_android.json and codebase_navigation_map_ios.json, then merges each into navigation_map_<platform>.json. Skips a platform if the git commit hash hasn't changed since last analysis.
---

> **Session data:** Read `OUTPUT_DIR`, `project`, `platform`, `udid`, and `config` from session memory (set by session-wizard). If any value is missing → load from `$OUTPUT_DIR/<project>/config.json` directly before proceeding.

# Codebase Screen Discovery

## Pre-flight Check

1. Load `localRepoPath` from `$OUTPUT_DIR/<project>/config.json` (already in session)
2. Ask: "Is the repository already cloned locally? If not, I'll clone it."
   - If not cloned: `git clone git@github.com:<repository>.git <localRepoPath>`
   - After cloning: `git -C <localRepoPath> submodule update --init --recursive`
3. Checkout dev branch: `git -C <localRepoPath> checkout dev && git -C <localRepoPath> pull`
4. Get current commit hash: `git -C <localRepoPath> rev-parse HEAD`

For each platform in `[android, ios]`:
- Check existing `$OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map_<platform>.json`:
  - If exists and `last_commit_hash` matches current → skip this platform: "Codebase nav map for <platform> is up to date (commit: <hash>). Skipping."
  - If exists but hash differs → "Repository has changed. Updating codebase nav map for <platform>..."
  - If not exists → proceed with full analysis for this platform

---

## Step 1 — Architecture Detection

Before dispatching subagents, do a quick scan of the repository root to detect the architecture:

- **MVVM detected** if any of these exist:
  - A git submodule folder containing `NavigationService`, `INavigationService`, or `PageViewModel`
  - A file named `NavigationRouts.cs`, `NavigationRoutes.cs`, `AppRoute.cs`, or `Routes.cs` with an enum of navigation keys
  - A base ViewModel class with a `NavigationEvent` or `Navigate(` method

- **Native detected** if any of these exist:
  - Android: `StartActivity(`, `SupportFragmentManager.BeginTransaction(`, `NavController.Navigate(`
  - iOS: `PushViewController(`, `PresentViewController(`, `PerformSegue(`

- **Architecture result:** `native` | `mvvm` | `mixed`

Store result as `detected_architecture`.

---

## Step 2 — Dispatch Shared MVVM Subagent (only if MVVM detected)

Skip this step entirely if `detected_architecture == "native"`.

> Analyze the shared MVVM layer of the .NET mobile repository at `<localRepoPath>`.
> The project may use a shared git submodule (e.g. `MobileCore`, `CoreMvvm`, `SharedCore`) and/or an app-specific Core project.
>
> **Priority files to find and read:**
>
> 1. **Navigation Routes enum** — search for files named `NavigationRouts.cs`, `NavigationRoutes.cs`, `AppRoute.cs`, `Routes.cs`, `PageKeys.cs`:
>    - Extract every enum value — this is the complete list of all navigable screens.
>
> 2. **Base ViewModel with navigation** — search for abstract ViewModel base classes that define:
>    - A navigation trigger method: `Navigate(`, `NavigateTo(`, `GoTo(`, `PushAsync(`, `GoToAsync(`
>    - A navigation result pattern: `Navigate<TResult>(`, callback-based, or messenger-based
>    - A `NavigateBack()` / `GoBack()` method
>    - A navigation event or delegate: `NavigationEvent`, `OnNavigate`, `NavigationRequested`
>
> 3. **NavigationArgs / NavigationPayload** — search for the class passed during navigation:
>    - What properties does it carry? (Route, Parameter, dialog flags, etc.)
>
> 4. **Navigation Parameters** — search for a `Parameters/` or `NavigationParams/` folder:
>    - List every parameter class and which route it belongs to
>
> 5. **Navigation Results / Messages** — search for a `Messages/` or `Results/` folder:
>    - List every result message class and which route triggers it
>
> 6. **Messenger / Event Bus** — search for pub/sub or messenger classes:
>    - `NavigationMessenger`, `IMessenger`, `EventAggregator`, `MvxMessenger`
>    - How are navigation results published and subscribed?
>
> **Return:**
> ```json
> {
>   "all_routes": ["Route1", "Route2"],
>   "navigation_trigger": "Navigate(NavigationRoutes, object) | GoToAsync(string) | other",
>   "navigation_event": "NavigationEvent | NavigationRequested | null",
>   "navigate_back": "NavigateBack() | GoBack() | null",
>   "result_pattern": "callback | messenger | task | null",
>   "parameters": {
>     "Route1": { "class": "Route1Parameter", "fields": ["field1", "field2"] }
>   },
>   "result_messages": {
>     "Route1": { "class": "Route1ResultMessage", "data_fields": ["field1"] }
>   }
> }
> ```

Store result as `shared_mvvm_analysis`.

---

## Step 3 — Dispatch Platform Subagents

Dispatch **two subagents in parallel** (or only those needing update per Pre-flight).
Pass `detected_architecture` and `shared_mvvm_analysis` (if available) as context.

---

### Subagent Android

> Analyze the Android-specific layer of the .NET mobile repository at `<localRepoPath>`.
> Detected architecture: `<detected_architecture>`
> MVVM analysis (if available): `<shared_mvvm_analysis>`
>
> Your job is to map every navigable screen in the Android project.
> Use the MVVM routes as starting point if available, then enrich with native navigation scan.
> For native-only apps, discover all screens from native patterns directly.
>
> **Part A — MVVM layer mapping (skip if no MVVM detected):**
>
> 1. **Navigation dispatcher** — search for a class that maps NavigationRoutes to Fragment/Activity classes:
>    - Could be named: `NavigationManager`, `NavigationExtensions`, `NavigationDispatcher`, `Navigator`
>    - Look for a switch/case or dictionary: `NavigationRoute.X → typeof(XFragment)` or `new XFragment()`
>    - Extract: which routes are Dialog fragments, which are BottomSheet, which are full screen
>
> 2. **Base Fragment with navigation binding** — search for the Fragment base class:
>    - How does it subscribe to the ViewModel navigation event?
>    - How does it call the navigation dispatcher?
>
> 3. **Main entry point** — search for `MainActivity.cs` or equivalent launcher:
>    - Initial fragment/navigation setup
>    - Bottom navigation tabs and their initial routes
>
> **Part B — Native navigation scan (always run, for all architectures):**
>
> 4. **Activity navigation** — search for:
>    - `StartActivity(new Intent(`, `StartActivityForResult(`
>    - Intent flags: `FLAG_ACTIVITY_NEW_TASK`, `FLAG_ACTIVITY_CLEAR_TOP`, `FLAG_ACTIVITY_SINGLE_TOP`, `FLAG_ACTIVITY_CLEAR_TASK`
>    - `Finish()`, `FinishAffinity()`, `FinishAndRemoveTask()`
>    - All Activity subclasses (files ending in `Activity.cs`)
>
> 5. **Fragment navigation** — search for:
>    - `SupportFragmentManager.BeginTransaction()`, `FragmentManager.BeginTransaction()`
>    - `.Add(`, `.Replace(`, `.Remove(` on fragment transactions
>    - `.AddToBackStack(`, `.PopBackStack(`, `.PopBackStackImmediate(`
>    - All Fragment subclasses (files ending in `Fragment.cs`)
>
> 6. **Navigation Component** — search for:
>    - NavGraph XML files in `res/navigation/*.xml` — parse all `<fragment>`, `<activity>`, `<action>`, `<argument>`
>    - `FindNavController(`, `NavController.Navigate(`, `NavController.PopBackStack(`
>    - `NavHostFragment`, `R.id.nav_` references
>
> 7. **Bottom Navigation / Tabs** — search for:
>    - `BottomNavigationView`, `NavigationView`, `TabLayout`, `ViewPager`, `ViewPager2`
>    - Menu XML in `res/menu/*.xml` — extract tab items with `id` and `title`
>    - `TabLayoutMediator`, `FragmentStateAdapter`
>
> 8. **Deep Link** — search for:
>    - `<intent-filter>` with `ACTION_VIEW` in `AndroidManifest.xml` — extract URL schemes and hosts
>    - `<deepLink` in NavGraph XML
>    - `Uri.Parse(`, `HandleDeepLink(`, custom scheme parsing in .cs files
>
> **For each screen found, record:**
> - Class name and file path
> - Navigation source: `mvvm_route` | `native_direct` | `nav_component` | `deep_link`
> - Navigation type: `fragment_replace` | `fragment_add` | `dialog_fragment` | `bottom_sheet` | `tab_switch` | `activity_intent` | `deep_link`
> - Parent screen
> - Tab group (if in bottom navigation)
> - Prerequisites (login required, specific data)
> - Key interactive elements (Button, EditText, RecyclerView IDs from layout XML or ContentDescription in .cs)
> - Navigation path from app launch
>
> Return JSON:
> ```json
> {
>   "platform": "android",
>   "project": "<project>",
>   "repository": "<org/repo>",
>   "branch": "dev",
>   "last_commit_hash": "<sha>",
>   "last_analyzed": "<ISO date>",
>   "discovery_method": "codebase",
>   "architecture": {
>     "pattern": "native | mvvm | mixed",
>     "launcher_activity": "<LauncherActivity>",
>     "navigation_dispatcher": "<NavigationManagerClass> | null",
>     "bottom_nav_tabs": ["Tab1", "Tab2"],
>     "has_nav_component": true,
>     "deep_link_schemes": ["scheme://"],
>     "has_compose": false
>   },
>   "authentication": {
>     "type": "custom | sso | standard",
>     "fields": ["field1", "field2"],
>     "screen_class": "<LoginActivity|LoginFragment>",
>     "route": "<LoginRoute | null>"
>   },
>   "entry_flow": ["<LauncherActivity>", "<SplashScreen>", "<LoginScreen>", "<HomeScreen>"],
>   "screens": {
>     "<ScreenName>": {
>       "class": "<ClassName>",
>       "file": "<relative/path/to/File.cs>",
>       "navigation_type": "fragment_replace | activity_intent | dialog_fragment | bottom_sheet | tab_switch | deep_link",
>       "navigation_source": "mvvm_route | native_direct | nav_component | deep_link",
>       "navigation_route": "<EnumValue | null>",
>       "path": "<LauncherActivity> → <Screen>",
>       "parent": "<ParentScreen>",
>       "tab": "<TabName | null>",
>       "is_dialog": false,
>       "is_bottom_sheet": false,
>       "prerequisites": ["login"],
>       "navigation_parameter": "<ParameterClass | null>",
>       "result_message": "<ResultClass | null>",
>       "deep_link_url": "<scheme://path | null>",
>       "interactive_elements": ["element_id_1", "element_id_2"]
>     }
>   }
> }
> ```

---

### Subagent iOS

> Analyze the iOS-specific layer of the .NET mobile repository at `<localRepoPath>`.
> Detected architecture: `<detected_architecture>`
> MVVM analysis (if available): `<shared_mvvm_analysis>`
>
> Your job is to map every navigable screen in the iOS project.
> Use the MVVM routes as starting point if available, then enrich with native navigation scan.
> For native-only apps, discover all screens from native patterns directly.
>
> **Part A — MVVM layer mapping (skip if no MVVM detected):**
>
> 1. **Navigation coordinator/dispatcher** — search for a class that maps NavigationRoutes to ViewControllers:
>    - Could be named: `AppCoordinator`, `NavigationCoordinator`, `Navigator`, `NavigationExtensions`
>    - Look for a switch/case or dictionary: `NavigationRoute.X → XViewController`
>    - Navigation methods: `PerformPush(`, `PerformModal(`, `PerformResetStack(`, `HandleNavigationRequest(`
>    - Mapping from routes to Storyboard names: `GetRoute(NavigationRoutes)` or equivalent
>
> 2. **Base ViewController with navigation binding** — search for the ViewController base class:
>    - How does it subscribe to ViewModel navigation event? (`DidMoveToParentViewController`, `ViewDidLoad`)
>    - How does it call the coordinator/dispatcher?
>
> 3. **Main entry point** — search for `AppDelegate.cs`:
>    - Initial coordinator/flow setup
>    - UIWindow, UINavigationController, UITabBarController creation
>
> **Part B — Native navigation scan (always run, for all architectures):**
>
> 4. **UINavigationController push/pop** — search for:
>    - `NavigationController.PushViewController(`, `PushViewController(`
>    - `NavigationController.PopViewController(`, `PopToRootViewController(`, `PopToViewController(`
>    - `NavigationController.SetViewControllers(`
>    - Any ViewController pushed directly outside a coordinator
>
> 5. **Modal Presentation** — search for:
>    - `PresentViewController(`, `DismissViewController(`
>    - `ModalPresentationStyle`, `UIModalPresentationStyle` values used
>    - `UISheetPresentationController`, `.Detents`, `.Medium`, `.Large`
>    - Any ViewController presented modally outside a coordinator
>
> 6. **UITabBarController** — search for:
>    - `UITabBarController`, `TabBarController`
>    - `ViewControllers = new UIViewController[]` assignments
>    - `SelectedIndex`, `TabBarItem.Title` values
>    - Tab structure: which ViewControllers per tab
>
> 7. **UISplitViewController** — search for:
>    - `UISplitViewController`, `SplitViewController`
>    - `ShowDetailViewController(`, master/detail ViewController assignments
>
> 8. **Deep Link** — search for:
>    - `OpenUrl(` in `AppDelegate.cs` — URL scheme handling
>    - `ContinueUserActivity(` — Universal Link handling
>    - URL schemes in `Info.plist`: `<key>CFBundleURLSchemes</key>`
>    - Associated Domains in `.entitlements` for Universal Links
>    - Custom deep link parsing logic in .cs files
>
> 9. **Storyboard Segue** — search in `.storyboard` files and .cs files:
>    - `PerformSegue(`, `PrepareForSegue(`
>    - `<segue` elements in .storyboard with `identifier=`
>    - `InstantiateViewController(` calls
>    - All `.storyboard` files — list initial ViewControllers and segue targets
>
> 10. **SwiftUI Navigation** — search for (if SwiftUI is used alongside .cs):
>    - `NavigationStack`, `NavigationLink`, `NavigationPath`
>    - `.navigationDestination(`, `.sheet(`, `.fullScreenCover(`
>    - Any `.swift` files with navigation declarations
>
> 11. **All ViewController files** — list all files ending in `ViewController.cs`:
>    - Match to NavigationRoute via coordinator mapping (if MVVM) or native call sites
>
> **For each screen found, record:**
> - Class name and file path
> - Storyboard name (if applicable)
> - Navigation source: `mvvm_route` | `native_direct` | `deep_link` | `segue` | `swiftui`
> - Navigation type: `push` | `modal` | `modal_nav` | `tab` | `split_master` | `split_detail` | `reset_stack` | `segue` | `sheet` | `deep_link` | `swiftui_link`
> - Parent screen
> - Tab group (if inside UITabBarController)
> - Prerequisites
> - Key interactive elements (UIButton, UITextField with AccessibilityIdentifier or AccessibilityLabel)
> - Navigation path from app launch
>
> Return JSON:
> ```json
> {
>   "platform": "ios",
>   "project": "<project>",
>   "repository": "<org/repo>",
>   "branch": "dev",
>   "last_commit_hash": "<sha>",
>   "last_analyzed": "<ISO date>",
>   "discovery_method": "codebase",
>   "architecture": {
>     "pattern": "native | mvvm | mixed",
>     "entry_point": "AppDelegate",
>     "coordinator": "<CoordinatorClass | null>",
>     "navigation_type": "coordinator | tab_bar | navigation_controller | mixed",
>     "tab_bar_items": ["Tab1", "Tab2"],
>     "deep_link_schemes": ["scheme://"],
>     "has_split_view": false,
>     "has_swiftui": false
>   },
>   "authentication": {
>     "type": "custom | sso | standard",
>     "fields": ["field1", "field2"],
>     "screen_class": "<LoginViewController>",
>     "storyboard": "<StoryboardName | null>",
>     "route": "<LoginRoute | null>"
>   },
>   "entry_flow": ["AppDelegate", "<InitialFlow>", "<LoginScreen>", "<HomeScreen>"],
>   "screens": {
>     "<ScreenName>": {
>       "class": "<ClassName>",
>       "file": "<relative/path/to/File.cs>",
>       "storyboard": "<StoryboardName | null>",
>       "navigation_type": "push | modal | modal_nav | tab | split_master | split_detail | reset_stack | segue | sheet | deep_link | swiftui_link",
>       "navigation_source": "mvvm_route | native_direct | deep_link | segue | swiftui",
>       "navigation_route": "<EnumValue | null>",
>       "path": "AppDelegate → <Screen>",
>       "parent": "<ParentScreen>",
>       "tab": "<TabName | null>",
>       "prerequisites": ["login"],
>       "navigation_parameter": "<ParameterClass | null>",
>       "result_message": "<ResultClass | null>",
>       "deep_link_url": "<scheme://path | null>",
>       "interactive_elements": ["element_id_1", "element_id_2"]
>     }
>   }
> }
> ```

---

## Step 4 — Save Platform Maps

Save each subagent result to its platform file:
- Android → `$OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map_android.json`
- iOS → `$OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map_ios.json`

---

## Step 5 — Merge into navigation_map_<platform>.json

For each platform updated in Step 3:

**If `appium_navigation_map_<platform>.json` exists → merge both:**

- Start from `codebase_navigation_map_<platform>.json` as base
- For each screen in `appium_navigation_map_<platform>.json`:
  - If screen exists in codebase map → enrich `interactive_elements` with appium findings, keep codebase `path`/`navigation_type`/`navigation_source`/`class`
  - If screen exists only in appium → add it with `"source": "appium_only"`
- For screens only in codebase → keep as-is with `"source": "codebase_only"`
- Set `"discovery_method": "merged"`, `"last_analyzed": <now>`, `"total_screens": <combined count>`

**If no `appium_navigation_map_<platform>.json` exists:**

Copy `codebase_navigation_map_<platform>.json` as-is to `navigation_map_<platform>.json`.

**Write results to:**
- `$OUTPUT_DIR/<project>/nav_maps/navigation_map_android.json`
- `$OUTPUT_DIR/<project>/nav_maps/navigation_map_ios.json`

---

Report:
```
✅ Codebase analysis complete
   Architecture detected   : native | mvvm | mixed
   Screens mapped (Android): N   (dialog: N, bottom sheet: N, tab: N, native: N)
   Screens mapped (iOS)    : N   (modal: N, push: N, tab: N, native: N)
   Codebase map Android    : $OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map_android.json
   Codebase map iOS        : $OUTPUT_DIR/<project>/nav_maps/codebase_navigation_map_ios.json
   Nav map Android updated : $OUTPUT_DIR/<project>/nav_maps/navigation_map_android.json  (merged | copied)
   Nav map iOS updated     : $OUTPUT_DIR/<project>/nav_maps/navigation_map_ios.json  (merged | copied)
   Commit hash             : abc123...
```

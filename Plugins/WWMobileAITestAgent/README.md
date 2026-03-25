# WWMobileAITestAgent

AI-powered mobile QA testing agent for WorkWave apps (PestPac, RealGreen, WinTeam, RouteManager).
Automates build deployment, login, screen discovery, and test execution on real devices and simulators via Appium.

---

## Prerequisites

### System Tools

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | `brew install python` |
| Java JDK | 11+ | `brew install openjdk@17` |
| Node.js | 18+ | `brew install node` |
| Xcode | latest | Mac App Store |
| Android SDK (adb) | any | Android Studio |
| Appium | 2.x+ | `npm install -g appium` |
| Appium XCUITest driver | latest | `appium driver install xcuitest` |
| Appium UIAutomator2 driver | latest | `appium driver install uiautomator2` |
| Firebase CLI | 13+ | `npm install -g firebase-tools` |
| ios-deploy | 1.12+ *(optional)* | `brew install ios-deploy` |

> `ios-deploy` is optional — the Appium XCUITest driver handles iOS physical device installation automatically.

### MCP Servers (required in Claude settings)

| MCP Server | Type | URL |
|------------|------|-----|
| Appium | stdio | configured via Claude Code MCP settings |
| claude.ai Atlassian | HTTP | `https://mcp.atlassian.com/v1/mcp` |
| claude.ai Figma | HTTP | `https://mcp.figma.com/v1/mcp` |
| Firebase | stdio | configured via Claude Code MCP settings |
| GitHub | stdio | configured via Claude Code MCP settings |

Run `/verify-environment` to check that all tools and MCP servers are correctly configured.

---

## How to Start

Open Claude Code in the plugin directory and run:

```
/startMobileTest
```

This launches the **Session Startup Wizard** which guides you through all setup steps.

---

## Wizard Steps

| Step | Name | Description |
|------|------|-------------|
| **0** | Output Directory | Set where all test data is saved (builds, credentials, reports, nav maps). Saved outside the plugin in `WWMobileTestAgentAIResults/`. |
| **1** | Environment Check | Verifies all required tools and MCP servers are installed. Offers to auto-install missing ones. |
| **2** | Firebase Keys | Scans your Firebase service account JSON files, auto-matches them to projects, and pre-populates project configs. |
| **3** | Select Project | Choose: PestPac / RealGreen / WinTeam / RouteManager |
| **4** | Select OS | Android or iOS |
| **5** | Select Device | Lists connected physical devices + available simulators/emulators |
| **6** | Select Build | Local `.ipa/.apk` / Firebase App Distribution / Use currently installed build |
| **7** | Deploy Build | Downloads (if Firebase) and installs the app on the selected device. Skipped if using the currently installed build. |
| **8** | Authentication | Uses saved credentials or prompts for login details |
| **9** | Navigation Map | Maps all app screens via: Automated Discovery / Codebase Analysis / Skip |
| **10** | Test Mode | Launches the selected test type |

---

## Commands

| Command | Description |
|---------|-------------|
| `/startMobileTest` | Start the full session wizard (recommended entry point) |
| `/getIosDeviceAndSimulator` | List all iOS physical devices and simulators |
| `/getAndroidDeviceAndSimulator` | List all Android physical devices and emulators |
| `/getFirebaseBuilds <project> <android\|ios>` | Fetch last 10 builds from Firebase App Distribution |

---

## Test Modes

### 1. Ticket-Driven Test (`/ticket-test`)

Tests a specific Jira ticket against its Acceptance Criteria.

1. Fetches ticket from Jira via Atlassian MCP
2. Retrieves Figma design if a figma.com URL is linked in the ticket
3. Identifies affected screens from the feature branch diff (GitHub)
4. Drives Appium to test each Acceptance Criterion
5. Generates Python/Appium auto-scripts saved to `auto-generated-scripts/ticket-tests-scripts/`
6. Saves results to `reports/<TICKET_ID>.md` (new runs prepended at the top)
7. Offers to run a full regression afterwards
8. Optionally creates Jira bug reports for each failure via Atlassian MCP

### 2. POM Auto-Generation (`/pom-test`)

Generates pytest + Appium Page Object Model test files for every screen in the navigation map.

- Creates `conftest.py`, `base_page.py`, per-screen page objects and test classes
- Also generates standalone autoscripts in `auto-generated-scripts/pom-tests-scripts/` (iOS + Android)
- Output: `$OUTPUT_DIR/<project>/test-pom-generated/`

Run generated tests:
```bash
cd "$OUTPUT_DIR/<project>/test-pom-generated"
pytest tests/ --platform ios --device-udid <udid> --bundle-id <bundleId> -v
```

### 3. Workflow Test (`/workflow-test`)

Runs a structured test workflow defined in a markdown file.

- Reads test phases from `$OUTPUT_DIR/<project>/test-workflow/*.md`
- Creates a starter file automatically if none exists
- Executes each step via Appium, logs pass/fail per step with screenshots on failure
- Generates reusable Python autoscripts after execution
- Generates a QA report at the end

---

## Navigation Map

The navigation map (`navigation_map.json`) is built by one or both discovery methods and merged automatically:

| Method | Description | Output file |
|--------|-------------|------------|
| **Automated Screen Discovery** | Explores the running app via Appium post-login | `appium_navigation_map.json` |
| **Codebase Screen Discovery** | Analyzes the `.NET Xamarin/MAUI` repository on the `dev` branch | `codebase_navigation_map.json` |

When both maps exist they are merged: the codebase map provides routes, ViewModels and architecture; the Appium map enriches interactive elements. The merged result is saved to `navigation_map.json`.

Codebase discovery is skipped automatically if the git commit hash hasn't changed since the last analysis.

---

## Output Directory Structure

All generated data is saved to `WWMobileTestAgentAIResults/` (location chosen at startup):

```
WWMobileTestAgentAIResults/
├── firebase_keys.json              ← Firebase key mapping (shared across projects)
├── PestPac/
│   ├── config.json                 ← project config (bundle IDs, auth schema, Firebase IDs)
│   ├── builds/                     ← downloaded .ipa / .apk files
│   ├── credentials/                ← saved login credentials (credentials.json)
│   ├── reports/                    ← QA reports (.md files with timestamps)
│   │   └── screenshots/            ← failure screenshots
│   ├── nav_maps/                   ← navigation maps
│   │   ├── navigation_map.json
│   │   ├── appium_navigation_map.json
│   │   └── codebase_navigation_map.json
│   ├── test-pom-generated/         ← POM pytest files (pytest + appium-python-client)
│   ├── test-workflow/              ← test workflow markdown files
│   ├── test-ticket-driven/         ← reusable workflow files generated from ticket tests
│   └── auto-generated-scripts/     ← standalone Python scripts (no pytest needed)
│       ├── helpers/                ← shared utilities (session, login, navigation)
│       │   ├── ios/
│       │   └── android/
│       ├── ticket-tests-scripts/
│       │   ├── ios/<TICKET_ID>/
│       │   └── android/<TICKET_ID>/
│       ├── pom-tests-scripts/
│       │   ├── ios/
│       │   └── android/
│       └── workflow-tests-scripts/
│           ├── ios/
│           └── android/
├── RealGreen/  ...
├── WinTeam/    ...
└── RouteManager/ ...
```

The plugin folder itself only stores skills and commands. The output directory pointer is saved to `~/.claude/ww-mobile-ai-test-agent-outputdir.txt` — outside the plugin so it survives version updates.

---

## Supported Projects

| Project | Auth Type | Bundle ID |
|---------|-----------|-----------|
| PestPac | SSO (email + password) | `com.workwave.pestpac` |
| RealGreen | Custom (companyNumber + employeeId + password) | `com.workwave.realgreen` |
| WinTeam | SSO (email + password) | `com.workwave.winteam` |
| RouteManager | Standard (email + password) | `com.workwave.routemanager` |

---

## iOS Physical Device — First-Time Setup

WebDriverAgent (WDA) must be built and signed once per Mac/device pair:

1. Open **Xcode → Settings → Accounts** and sign in with the Apple ID linked to your dev team
2. The agent detects your signing certificate and builds WDA automatically on first run
3. Subsequent sessions reuse the pre-built WDA (fast startup via `usePrebuiltWDA: true`)

The WorkWave team ID (`xcodeOrgId: 8V5NXR3J7H`) and any Ad Hoc provisioning profiles found on the machine are applied automatically.

---

## Firebase Keys

Place Firebase service account JSON files anywhere on your machine (e.g. `~/.config/firebase/`).
The wizard (Step 2) scans the folder, auto-matches keys to projects by `project_id`, fetches Firebase App IDs from the API, and pre-populates each project's `config.json`.

The mapping is persisted to `$OUTPUT_DIR/firebase_keys.json` and reused in future sessions.

---

## Auto-Generated Scripts

After every test run (ticket, POM, or workflow), the agent generates standalone Python scripts under `auto-generated-scripts/`. These scripts:

- Run outside Claude Code with a single `python script.py` command
- Use shared helpers (`helpers/session.py`, `helpers/login.py`, `helpers/navigation.py`) with platform-specific factories (`helpers/ios/`, `helpers/android/`)
- Are regenerated on each run (latest run = most accurate)
- Shared helper files are never overwritten — only new functions are appended

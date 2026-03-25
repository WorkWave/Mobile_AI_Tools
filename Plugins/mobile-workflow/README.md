+# mobile-ui-builder MCP Server

A Model Context Protocol (MCP) server that validates and generates mobile UI files for both **iOS** (Xcode `.storyboard`) and **Android** (layout XML). It runs as a local stdio process and exposes 11 tools to Claude.

---

## Included Skills

This plugin bundles two skills that are automatically available after installation:

### `code-convention`
Enforces the team's C#/.NET MAUI code-writing style. Applied automatically when writing code (not user-invocable directly).

- Member ordering: injections → public properties → private properties → constructor → public methods → private methods
- Avoids `async void` except for event handlers; uses `async Task` for all other async methods

### `jira-to-implementation`
End-to-end implementation workflow from a Jira ticket ID, acting as a Senior Mobile Developer for iOS and Android.

Invoke with: `/jira-to-implementation`

Usage:

    Ticket: [PROJ-XXX]
    Additional notes: [optional context]

---

## Requirements

- Python 3.13+
- Claude Code CLI

### Installing Python 3.13+

**macOS (Homebrew — recommended):**
```bash
brew install python@3.13
```

**macOS (official installer):**
Download from [python.org/downloads](https://www.python.org/downloads/) and run the `.pkg` installer.

After installing, verify:
```bash
python3 --version  # should print Python 3.13.x or higher
```

---

## Installation

### Option A — Install as a Claude Code Plugin (recommended)

This is the easiest way to get the MCP server, skills, and agents all configured automatically.

**Step 1** — Clone the repository and set up the Python environment:

```bash
git clone <repo-url> ~/mobile-workflow
cd ~/mobile-workflow
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Step 2** — Add the marketplace from the Git repo in the Claude Code CLI prompt:

```
/plugin marketplace add <repo-url>
```

**Step 3** — Install the plugin from the Discover tab:

```
/plugin
```

Navigate to **Discover**, select **mobile-ui-builder**, and choose your scope (User, Project, or Local).

**Step 4** — Reload plugins:

```
/reload-plugins
```

That's it. The MCP server, skills (`mobile-ui-builder`, `code-convention`, `jira-to-implementation`), and agents are now active.

> **Note:** The MCP server runs locally — make sure you have completed Step 1 (clone + Python venv setup) before installing the plugin, as Claude Code will launch the server from your local clone.

---

### Option B — Manual Setup

### Setup

```bash
cd storyboard_mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Claude Code CLI config

**Option 1 — local (only for you):**

```bash
claude mcp add --transport stdio mobile-ui-builder -- \
  /path/to/storyboard_mcp/.venv/bin/python \
  /path/to/storyboard_mcp/server/server.py
```

**Option 2 — project-level `.mcp.json` (shared with the team via Git):**

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "mobile-ui-builder": {
      "type": "stdio",
      "command": "/path/to/storyboard_mcp/.venv/bin/python",
      "args": ["/path/to/storyboard_mcp/server/server.py"],
      "env": {
        "FIGMA_TOKEN": "${FIGMA_TOKEN}"
      }
    }
  }
}
```

### FIGMA_TOKEN (optional)

Required only for `figma_export_to_xcassets` and `figma_export_to_drawable`.

**Step 1** — Create a personal access token in Figma:
Figma → top-left menu → **Settings** → **Security** → **Personal access tokens** → **Generate new token**
Set scope: *File content* → Read. Copy the token immediately (shown only once).

**Step 2** — Pass the token directly when registering the MCP server with `-e`:

```bash
claude mcp add --transport stdio mobile-ui-builder \
  -e FIGMA_TOKEN=figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
  -- /path/to/storyboard_mcp/.venv/bin/python \
     /path/to/storyboard_mcp/server/server.py
```

Claude Code stores the token in `~/.claude.json` and injects it at startup. This works regardless of how Claude Code is launched (terminal, GUI, Spotlight).

> **Why not `~/.zshrc`?** Shell profile variables are only available when Claude Code is launched from an interactive terminal session. If opened from the Dock or Spotlight, `~/.zshrc` is never sourced and `${FIGMA_TOKEN}` in `.mcp.json` would be empty.

**Step 3** — Verify the token is registered:

```bash
claude mcp get mobile-ui-builder   # should show FIGMA_TOKEN in the env section
```

> **Adding or updating the token later:** run the same `claude mcp add` command again with the new token — it overwrites the existing registration. Restart Claude Code afterwards to apply the change.

---

## Tools

### iOS Tools

#### 1. `validate_ios_storyboard`

Validates a `.storyboard` file on disk.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | string | Yes | Absolute path to the `.storyboard` file |
| `checks` | string[] | No | Subset of `["schema", "connections", "constraints", "guidelines"]`. Defaults to all four. |

**Returns:** JSON report with `summary.status` (`"PASS"` / `"FAIL"`), `summary.total_errors`, `summary.total_warnings`, and per-check results.

---

#### 2. `validate_ios_storyboard_content`

Same as `validate_ios_storyboard` but accepts raw XML instead of a file path. Useful when working with generated XML before saving.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `content` | string | Yes | Raw `.storyboard` XML string |
| `checks` | string[] | No | Subset of `["schema", "connections", "constraints", "guidelines"]`. Defaults to all four. |

---

#### 3. `generate_ios_ui_from_image`

Takes a UI screenshot or Figma export and generates a `.storyboard`. Claude visually analyzes the image, infers the layout, and calls `generate_ios_ui_from_layout` automatically.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `image_path` | string | Yes | Path to PNG, JPEG, or WebP image |
| `output_path` | string | No | Where to write the `.storyboard` file |
| `hints` | string | No | Free-text notes to guide interpretation (e.g. `"login screen, use UITableViewController"`) |
| `custom_class_prefix` | string | No | Prefix for generated ViewController class names (e.g. `"RG"` → `RGLoginViewController`) |

---

#### 4. `generate_ios_ui_from_layout`

Generates valid Xcode `.storyboard` XML from a **Layout JSON** description.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `layout` | object or string | Yes | Layout JSON (see schema below) |
| `output_path` | string | No | Path to write the `.storyboard` file |
| `validate` | boolean | No | Run validation on the output. Defaults to `true`. |

---

#### 5. `figma_export_to_xcassets`

Exports a Figma component as PNG at 1x / 2x / 3x (or as PDF vector) into an Xcode `.xcassets` imageset.

Requires `FIGMA_TOKEN` in the environment.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `figma_url` | string | Yes* | Figma share URL containing `?node-id=…` |
| `file_key` | string | Yes* | Figma file key (alternative to `figma_url`) |
| `node_id` | string | Yes* | Figma node ID, e.g. `"12:34"` (alternative to `figma_url`) |
| `xcassets_path` | string | Yes | Absolute path to the `.xcassets` folder |
| `asset_name` | string | Yes | Imageset name, e.g. `"icon-arrow"` |
| `scales` | integer[] | No | Scales to export: `[1, 2, 3]` (default) |
| `format` | string | No | `"png"` (default) or `"pdf"` (vector, recommended for icons) |
| `render_as_template` | boolean | No | `true` for tintable/monochrome icons |

*Provide either `figma_url` OR both `file_key` + `node_id`.

---

#### 6. `add_image_to_xcassets`

Adds a local PNG or HTTPS image as one scale variant of an existing imageset. Other scale variants are preserved.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `image_source` | string | Yes | Local file path or HTTPS URL |
| `xcassets_path` | string | Yes | Absolute path to the `.xcassets` folder |
| `asset_name` | string | Yes | Imageset name |
| `scale` | integer | No | Density scale: `1`, `2`, or `3` (default `2`) |
| `render_as_template` | boolean | No | `true` for tintable icons |

---

### Android Tools

#### 7. `generate_android_ui_from_image`

Takes a UI screenshot or Figma export and prepares it for Android layout generation. Claude visually analyzes the image and calls `generate_android_ui_from_json` automatically.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `image_path` | string | Yes | Path to PNG, JPEG, or WebP image |
| `output_path` | string | No | Where to write the layout XML file |
| `hints` | string | No | Free-text notes to guide interpretation (e.g. `"login screen"`) |

---

#### 8. `generate_android_ui_from_json`

Generates Android `res/layout` XML, `res/values/strings.xml`, and `res/values/dimens.xml` from an **Android JSON** layout description.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `layout` | object or string | Yes | Android JSON (see schema below) |
| `output_path` | string | No | Path to write the layout XML file |
| `validate` | boolean | No | Run all 4 validators on the output. Defaults to `true`. |

---

#### 9. `validate_android_layout`

Validates an Android layout XML file or raw XML string. Runs four checks: layout (schema + constraints), naming (IDs + filename), material (Material 3), guidelines (accessibility, strings, colors, dimensions).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `path` | string | Yes* | Absolute path to the layout XML file |
| `content` | string | Yes* | Raw layout XML string (alternative to `path`) |
| `checks` | string[] | No | Subset of `["layout", "naming", "material", "guidelines"]`. Defaults to all four. |
| `filename` | string | No | Filename hint for naming validator (e.g. `"activity_login.xml"`) |

*Provide either `path` or `content`.

---

#### 10. `figma_export_to_drawable`

Exports a Figma component to Android `res/drawable-*` density directories.

PNG exports all 5 density buckets: `mdpi` / `hdpi` / `xhdpi` / `xxhdpi` / `xxxhdpi`. SVG converts to an Android Vector Drawable XML file.

Requires `FIGMA_TOKEN` in the environment.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `figma_url` | string | Yes* | Figma share URL containing `?node-id=…` |
| `file_key` | string | Yes* | Figma file key (alternative to `figma_url`) |
| `node_id` | string | Yes* | Figma node ID (alternative to `figma_url`) |
| `drawable_path` | string | Yes | Absolute path to the `res/` directory |
| `asset_name` | string | Yes | Drawable name, e.g. `"ic_arrow"` |
| `format` | string | No | `"png"` (default) or `"svg"` (Vector Drawable) |

*Provide either `figma_url` OR both `file_key` + `node_id`.

---

#### 11. `add_image_to_drawable`

Adds a local PNG or HTTPS image to one `res/drawable-{density}/` bucket. Files in other density buckets are preserved.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `image_source` | string | Yes | Local file path or HTTPS URL |
| `drawable_path` | string | Yes | Absolute path to the `res/` directory |
| `asset_name` | string | Yes | Drawable name, e.g. `"ic_arrow"` |
| `density` | string | No | Density bucket: `mdpi`, `hdpi`, `xhdpi`, `xxhdpi`, `xxxhdpi` (default `xxhdpi`) |

---

## Figma → iOS workflow

```
1. Open Figma, right-click a component → "Copy link"
2. Ask Claude: "Export the icon at <url> as 'icon-arrow' into ~/MyApp/Assets.xcassets"
   → figma_export_to_xcassets → imageset written to disk
3. Ask Claude: "Generate a storyboard from this design"
   → generate_ios_ui_from_image → generate_ios_ui_from_layout → storyboard written
4. Open Xcode — asset and storyboard are ready
```

## Figma → Android workflow

```
1. Open Figma, right-click a component → "Copy link"
2. Ask Claude: "Export the icon at <url> as 'ic_arrow' into ~/MyApp/res/"
   → figma_export_to_drawable → drawable-* directories written
3. Ask Claude: "Generate an Android layout from this design"
   → generate_android_ui_from_image → generate_android_ui_from_json → layout XML written
4. Open Android Studio — drawable and layout are ready
```

---

## Example Prompts

### Export assets from Figma

**iOS (xcassets):**
```
Export the "Add" button icon from the Figma component to xcassets.

Figma URL: https://www.figma.com/design/AbCdEf123/MyApp?node-id=12-34
xcassets folder: /Users/me/MyApp/RG.Mobile.iOS/Assets.xcassets
Asset name: icon-add
Format: pdf
```

**Android (drawable):**
```
Export the logo from Figma as a vector SVG for Android.

Figma URL: https://www.figma.com/design/AbCdEf123/MyApp?node-id=45-67
Drawable folder: /Users/me/MyApp/RG.Mobile.Android/Resources/drawable
Asset name: ic_logo
Format: svg
```

---

### Generate an iOS storyboard from a Figma design

```
Look at this Figma design for the app login screen:
https://www.figma.com/design/AbCdEf123/MyApp?node-id=10-20

Generate an iOS storyboard (.storyboard) that faithfully reproduces the layout.
The screen has:
- Logo centered at the top
- Email field (UITextField)
- Password field (UITextField)
- Primary "Login" button
- "Forgot password?" link

Output path: /Users/me/MyApp/RG.Mobile.iOS/Storyboards/Login.storyboard
Validate the generated storyboard.
```

---

### Generate an Android layout from a Figma design

```
Look at this Figma design for the Job Detail screen:
https://www.figma.com/design/AbCdEf123/MyApp?node-id=55-78

Generate the Android XML layout following the project conventions:
- Layout file: fragment_job_detail.xml
- Component IDs with format: fragment_job_detail_{type}_{purpose}
  e.g.: fragment_job_detail_tv_title, fragment_job_detail_btn_start

Output path: /Users/me/MyApp/RG.Mobile.Android/Resources/layout/fragment_job_detail.xml
Validate the generated layout.
```

---

### Full workflow (assets + UI, both platforms)

```
I have a Figma design for the AI Assistant screen:
https://www.figma.com/design/AbCdEf123/MyApp?node-id=100-200

Follow these steps:
1. Export the microphone icon (node-id: 101-10) as PDF to xcassets as "icon-microphone"
2. Export the send icon (node-id: 101-11) as PDF to xcassets as "icon-send"
3. Generate the iOS storyboard for the chat screen
4. Generate the corresponding Android fragment layout

Paths:
- xcassets: /Users/me/MyApp/RG.Mobile.iOS/Assets.xcassets
- Storyboard output: /Users/me/MyApp/RG.Mobile.iOS/Storyboards/AiAssistant.storyboard
- Android layout: /Users/me/MyApp/RG.Mobile.Android/Resources/layout/fragment_ai_assistant.xml
```

---

**Tips:**
- The `node-id` is found in the Figma URL after `?node-id=` (e.g. `12-34`)
- `FIGMA_TOKEN` environment variable must be set to access Figma
- For icons on iOS: use `pdf` format (vector, any resolution)
- On Android: prefer `svg` → it is converted to a Vector Drawable XML

---

## iOS Layout JSON Schema

The Layout JSON is the data model for `generate_ios_ui_from_layout`.

### Single ViewController (minimal)

```json
{
  "name": "my-vc",
  "viewController": {
    "type": "UIViewController",
    "customClass": "MyViewController",
    "isInitial": true,
    "views": [],
    "constraints": [],
    "outlets": [],
    "segues": []
  }
}
```

### ViewController fields

| Field | Type | Description |
|---|---|---|
| `type` | string | `UIViewController`, `UITableViewController`, `UINavigationController`, etc. |
| `customClass` | string | Swift class name (e.g. `RGLoginViewController`) |
| `title` | string | Scene title shown in Interface Builder |
| `isInitial` | boolean | Marks as the initial VC (entry point arrow) |
| `views` | View[] | Top-level subviews of the root view |
| `constraints` | Constraint[] | Auto Layout constraints |
| `outlets` | Outlet[] | `@IBOutlet` connections |
| `segues` | Segue[] | Segue transitions to other scenes |

### View object

```json
{
  "id": "lbl-title",
  "type": "UILabel",
  "text": "Hello",
  "accessibilityLabel": "Title",
  "subviews": []
}
```

Common `type` values: `UILabel`, `UIButton`, `UITextField`, `UITextView`, `UIImageView`, `UIView`, `UIStackView`, `UITableView`, `UICollectionView`, `UIScrollView`, `UISwitch`, `UISlider`, `UIActivityIndicatorView`.

### Constraint object

**Shorthand (anchor to superview):**
```json
{ "id": "c-lbl-top", "item": "lbl-title", "attribute": "top", "constant": 20 }
```

**Full form (between two views):**
```json
{
  "id": "c-lbl-leading",
  "firstItem": "lbl-title", "firstAttribute": "leading",
  "secondItem": "lbl-subtitle", "secondAttribute": "leading",
  "constant": 0
}
```

---

## Android JSON Schema

The Android JSON is the data model for `generate_android_ui_from_json`.

### Minimal example

```json
{
  "screen_name": "LoginScreen",
  "root_layout": "ConstraintLayout",
  "views": [
    {
      "id": "activity_login_btn_login",
      "type": "MaterialButton",
      "style": "@style/Widget.Material3.Button",
      "text": "@string/login",
      "layout_width": "match_parent",
      "layout_height": "wrap_content",
      "constraints": {
        "bottom_to_bottom": "parent",
        "start_to_start": "parent",
        "end_to_end": "parent"
      },
      "margin_bottom": "16dp"
    }
  ],
  "strings": {
    "login": "Login"
  }
}
```

### Root fields

| Field | Type | Description |
|---|---|---|
| `screen_name` | string | Screen name (used as a label, not written to XML) |
| `root_layout` | string | `ConstraintLayout` (default), `LinearLayout`, `FrameLayout`, `CoordinatorLayout` |
| `views` | View[] | Top-level child views |
| `strings` | object | String resource entries written to `strings.xml` |

### View fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Resource ID in snake_case, e.g. `activity_login_btn_login` |
| `type` | string | `MaterialButton`, `TextInputLayout`, `TextInputEditText`, `RecyclerView`, `MaterialCardView`, `Toolbar`, etc. |
| `layout_width` | string | `match_parent`, `wrap_content`, or fixed dp value |
| `layout_height` | string | `match_parent`, `wrap_content`, or fixed dp value |
| `constraints` | object | ConstraintLayout anchors: `top_to_top`, `bottom_to_bottom`, `start_to_start`, `end_to_end`, etc. |
| `text` | string | Use `@string/key` reference (hardcoded strings fail validation) |
| `hint` | string | Use `@string/key` reference |
| `style` | string | Material 3 style, e.g. `@style/Widget.Material3.Button` |
| `input_type` | string | `textEmailAddress`, `textPassword`, etc. |
| `text_style` | string | Material text appearance: `headline1`–`headline6`, `body1`, `body2`, `caption`, etc. |
| `content_description` | string | Accessibility label for ImageView/ImageButton |
| `margin_top/bottom/start/end` | string | Margin in dp, e.g. `"16dp"` |
| `children` | View[] | Nested views (e.g. `TextInputEditText` inside `TextInputLayout`) |

### ID naming convention

Format: `{screen_type}_{component_type}_{purpose}`

| Screen type | Component prefixes |
|---|---|
| `activity_login` | `btn` Button, `et` EditText / TextInputEditText, `tv` TextView, `til` TextInputLayout |
| `fragment_home` | `rv` RecyclerView, `iv` ImageView, `cv` CardView, `tb` Toolbar |

Examples: `activity_login_btn_login`, `fragment_home_rv_feed`, `dialog_confirm_tv_message`

---

## iOS Validation Checks

| Check | What it does |
|---|---|
| `schema` | Verifies required XML attributes, known element types, `targetRuntime`, `useAutolayout`, etc. |
| `connections` | Detects orphaned `@IBOutlet` / `@IBAction` references that point to missing view IDs |
| `constraints` | Flags potentially ambiguous or conflicting `NSLayoutConstraint` configurations |
| `guidelines` | Enforces Apple iOS HIG and Xcode storyboard best practices |

---

## Android Validation Checks

| Check | What it does |
|---|---|
| `layout` | XML parse, missing `layout_width`/`layout_height`, broken constraint references, nesting depth |
| `naming` | IDs must be `snake_case`, interactive elements must have an ID, filename must match known prefixes |
| `material` | Flags legacy components (`Button`, `EditText`, `CardView`) that should use Material 3 equivalents |
| `guidelines` | Hardcoded strings, hardcoded hex colors, ImageView without contentDescription, missing touch targets (48dp), ScrollView with multiple children |

---

## Security

### File path restrictions

All tools that read or write files only accept paths under your **home directory** or the **server's launch directory**. Paths outside these roots are rejected:

```
Path '/etc/passwd' is outside the allowed roots.
Only paths under your home directory or current working directory are allowed.
```

### HTTPS-only image downloads

Image download tools only accept `https://` URLs. Plain `http://` URLs are rejected:

```
Only HTTPS downloads are allowed. Got: 'http://...'
```

---

## Project Structure

```
storyboard_mcp/
├── requirements.txt
├── tests/
│   ├── test_shared.py              # Tests for shared module
│   ├── test_android_generator.py   # Tests for Android layout generator
│   └── test_android_validators.py  # Tests for Android validators
└── server/
    ├── server.py                   # MCP server entry point (11 tools)
    ├── shared/
    │   ├── common.py               # Issue/result types shared by all validators
    │   ├── figma_client.py         # Figma REST API client (iOS + Android)
    │   └── image_analyzer.py       # Image → base64 loader for Claude vision
    ├── ios/
    │   └── validators/
    │       ├── schema_validator.py         # XML schema checks
    │       ├── connection_validator.py     # Outlet/action connection checks
    │       ├── constraint_validator.py     # Auto Layout constraint checks
    │       ├── guidelines_validator.py     # Apple HIG / best-practice checks
    │       ├── storyboard_generator.py     # Layout JSON → storyboard XML
    │       └── xcassets_manager.py         # Figma export + xcassets management
    └── android/
        ├── layout_generator.py             # Android JSON → layout XML + strings + dimens
        ├── drawable_manager.py             # Figma export + res/drawable-* management
        └── validators/
            ├── layout_validator.py         # XML schema + constraint checks
            ├── naming_validator.py         # ID + filename naming conventions
            ├── material_validator.py       # Material 3 component checks
            └── guidelines_validator.py     # Accessibility, strings, colors, dimensions
```

---

## Running Tests

```bash
cd storyboard_mcp
python3 -m pytest tests/ -v
```

32 tests covering shared utilities, Android layout generator, and all 4 Android validators.

---

## Changelog

### 2026-03-19 — Android support + rename to mobile-ui-builder

| # | Change | Details |
|---|---|---|
| 1 | Renamed from `storyboard-validator` to `mobile-ui-builder` | Server name updated; MCP config entry renamed |
| 2 | Shared module extracted | `server/shared/` with `common.py`, `figma_client.py`, `image_analyzer.py` — used by both iOS and Android |
| 3 | iOS files reorganized | All iOS validators moved to `server/ios/validators/` |
| 4 | iOS tool names updated | `validate_storyboard` → `validate_ios_storyboard`, `generate_storyboard_from_*` → `generate_ios_ui_from_*` |
| 5 | Android layout generator | `generate_android_ui_from_image` + `generate_android_ui_from_json` — supports ConstraintLayout, LinearLayout, Material 3 components, nested views, touch targets |
| 6 | Android drawable manager | `figma_export_to_drawable` + `add_image_to_drawable` — all 5 density buckets (mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi), SVG→AVD via `svg2vectordrawable` |
| 7 | Android validators | 4 checks: layout (schema + constraints), naming (snake_case IDs), material (Material 3), guidelines (accessibility, strings, colors, touch targets) |
| 8 | pytest added | 32 tests covering shared module, Android generator, and all 4 Android validators |

### 2026-03-18 — Security and bug fixes

| # | Change | Details |
|---|---|---|
| 1 | File path sandboxing | All file read/write operations reject paths outside the home directory or launch directory |
| 2 | HTTPS-only downloads | Image download tools reject `http://` URLs |
| 3 | Generator state isolation | ID generation cache is now local per call — no state leakage between concurrent calls |
| 4 | `backgroundColor: null` no longer crashes | `_add_color` silently skips non-string, non-dict values |
| 5 | System color name doubling fixed | `"systemBackgroundColor"` no longer becomes `"systemBackgroundColorColor"` |
| 6 | Constraint conflict detection handles reversed item pairs | `(A → B)` and `(B → A)` correctly identified as the same relationship |

### 2026-03-06 — PDF export for xcassets

Added `format: "pdf"` option to `figma_export_to_xcassets` for single-file vector assets.

### 2026-03-05 — iOS generator and validator bug fixes

Multiple fixes to storyboard generator (constraints, outlets, actions, `backgroundColor` dict support) and constraint validator (false positive fixes for `UIStackView` children, safe area layout guides, intrinsic-size controls).

### 2026-03-05 — Apple iOS HIG guidelines

New `guidelines` validation check enforcing Auto Layout flags, safe areas, trait collections, accessibility labels, Dynamic Type, semantic colors, cell reuse identifiers, and storyboard identifiers.
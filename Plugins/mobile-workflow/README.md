# mobile-workflow Plugin

A Claude Code plugin for end-to-end mobile development on iOS and Android.

**Includes:**
- **MCP server** (`mobile-ui-builder`) — 11 tools for generating and validating iOS storyboards and Android XML layouts, and exporting Figma assets
- **Skills** — `mobile-ui-builder`, `code-convention`, `code-review`, `jira-to-implementation`
- **Commands** — pre-implementation, implement, testing, post-implementation

---

## Requirements

- Claude Code CLI (latest)
- Python 3.13+ — the server checks the version at startup and **installs it automatically via Homebrew** if it's missing or too old. If Homebrew is not available, it prints a clear error with instructions.

---

## Installation

### Step 1 — Add the marketplace

In the Claude Code CLI prompt:

```
/plugin marketplace add github:WorkWave/Mobile-AI-Tools
```

### Step 2 — Install the plugin

```
/plugin
```

Navigate to **Discover**, select **mobile-workflow**, and choose your scope (User or Local).

### Step 3 — Set the FIGMA_TOKEN (optional)

Required only for `figma_export_to_xcassets` and `figma_export_to_drawable`. If you only use screenshots or local images, skip this step.

It must be set in `~/.claude/settings.json` — not in `.zshrc`, because Claude Code may launch without a shell session (Dock, Spotlight).

**Get a token:**
1. Figma → top-left menu → **Settings** → **Security** → **Personal access tokens**
2. **Generate new token** — set scope: *File content → Read*
3. Copy it immediately (shown only once)

**Add it to `~/.claude/settings.json`:**

Open the file and add an `env` block (merge with existing content, do not replace):

```json
{
  "env": {
    "FIGMA_TOKEN": "figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

### Step 4 — Reload plugins

```
/reload-plugins
```

### Step 5 — Verify the MCP server is connected

```
/mcp
```

`mobile-ui-builder` should appear with status **connected**.

> The first connection triggers automatic venv creation and dependency install — this takes ~10 seconds. Subsequent startups are instant.

---

## FIGMA_TOKEN: why `~/.claude/settings.json` and not `.zshrc` (when needed)

The plugin's `.mcp.json` injects `FIGMA_TOKEN` from the process environment:

```json
{
  "mobile-ui-builder": {
    "type": "stdio",
    "command": "${CLAUDE_PLUGIN_ROOT}/start-server.sh",
    "env": {
      "FIGMA_TOKEN": "${FIGMA_TOKEN}"
    }
  }
}
```

If Claude Code is launched from the Dock or Spotlight, `~/.zshrc` is never sourced and `${FIGMA_TOKEN}` resolves to an empty string — causing the MCP server to fail at connection time. Setting it in `~/.claude/settings.json` ensures it is always available regardless of how Claude Code is launched.

---

## Included Skills

### `mobile-ui-builder`
Generate and validate iOS storyboards and Android XML layouts from Figma URLs or screenshots. Dispatch parallel iOS and Android agents.

Invoke with: `/mobile-ui-builder`

### `code-convention`
Enforces the team's C#/.NET MAUI code-writing style. Applied automatically when writing code.

### `code-review`
Reviews code against team standards, patterns, and security practices.

Invoke with: `/mobile-workflow:code-review`

### `jira-to-implementation`
End-to-end implementation from a Jira ticket ID, acting as a Senior Mobile Developer for iOS and Android.

Invoke with: `/jira-to-implementation`

Usage:
```
Ticket: [PROJ-XXX]
Additional notes: [optional context]
```

---

## MCP Tools

### iOS

| Tool | Description |
|---|---|
| `validate_ios_storyboard` | Validates a `.storyboard` file (schema, connections, constraints, guidelines) |
| `validate_ios_storyboard_content` | Same as above but accepts raw XML instead of a file path |
| `generate_ios_ui_from_image` | Generates a `.storyboard` from a screenshot or Figma export |
| `generate_ios_ui_from_layout` | Generates a `.storyboard` from a Layout JSON description |
| `figma_export_to_xcassets` | Exports a Figma component to an Xcode `.xcassets` imageset — requires `FIGMA_TOKEN` |
| `add_image_to_xcassets` | Adds a local or HTTPS image to an existing imageset |
| `add_svg_asset` | Adds an SVG as a PDF asset to `.xcassets` |

### Android

| Tool | Description |
|---|---|
| `generate_android_ui_from_image` | Generates an Android layout XML from a screenshot or Figma export |
| `generate_android_ui_from_json` | Generates layout XML + strings.xml + dimens.xml from an Android JSON description |
| `validate_android_layout` | Validates layout XML (schema, naming, Material 3, accessibility) |
| `figma_export_to_drawable` | Exports a Figma component to `res/drawable-*` directories — requires `FIGMA_TOKEN` |
| `add_image_to_drawable` | Adds a local or HTTPS image to a drawable density bucket |

---

## Example Prompts

### Generate a storyboard from a Figma design

```
Look at this Figma design for the login screen:
https://www.figma.com/design/AbCdEf123/MyApp?node-id=10-20

Generate an iOS storyboard that reproduces the layout.
Output path: /Users/me/MyApp/RG.Mobile.iOS/Storyboards/Login.storyboard
```

### Generate an Android layout from a Figma design

```
Look at this Figma design for the Job Detail screen:
https://www.figma.com/design/AbCdEf123/MyApp?node-id=55-78

Generate the Android XML layout:
- Layout file: fragment_job_detail.xml
- Output path: /Users/me/MyApp/RG.Mobile.Android/Resources/layout/fragment_job_detail.xml
```

### Export a Figma icon to xcassets

```
Export the "Add" button icon from Figma to xcassets.

Figma URL: https://www.figma.com/design/AbCdEf123/MyApp?node-id=12-34
xcassets folder: /Users/me/MyApp/RG.Mobile.iOS/Assets.xcassets
Asset name: icon-add
Format: pdf
```

### Export a Figma icon to Android drawable

```
Export the logo from Figma as a vector SVG for Android.

Figma URL: https://www.figma.com/design/AbCdEf123/MyApp?node-id=45-67
Drawable folder: /Users/me/MyApp/RG.Mobile.Android/Resources/drawable
Asset name: ic_logo
Format: svg
```

---

## Running Tests

```bash
cd /Users/matteopiovan/Mobile_AI_Tools/Plugins/mobile-workflow
python3 -m pytest tests/ -v
```

---

## Project Structure

```
mobile-workflow/
├── start-server.sh             # MCP server launcher (auto-creates venv on first run)
├── requirements.txt
├── .mcp.json                   # MCP server config used by the plugin
├── .claude-plugin/plugin.json  # Plugin manifest
├── skills/                     # mobile-ui-builder, code-convention, code-review
├── commands/                   # pre-implementation, implement, testing, post-implementation
├── tests/
└── server/
    ├── server.py               # MCP entry point (11 tools)
    ├── shared/                 # common.py, figma_client.py, image_analyzer.py
    ├── ios/validators/         # schema, connections, constraints, guidelines, generator, xcassets
    └── android/                # layout_generator, drawable_manager, validators/
```
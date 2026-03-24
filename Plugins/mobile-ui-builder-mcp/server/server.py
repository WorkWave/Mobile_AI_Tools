"""
MCP Server — Storyboard Validator + Generator
"""

import asyncio
import base64
import json
import mimetypes
from pathlib import Path
from mcp.server import Server

# NOTE: _ALLOWED_ROOTS is evaluated once at module load time.
# Path.home() is stable; Path.cwd() reflects the server's launch directory.
_ALLOWED_ROOTS = (Path.home(), Path.cwd())

def _safe_path(raw: str, must_exist: bool = False) -> Path:
    """
    Resolve a caller-supplied path and verify it falls under an allowed root.
    Raises ValueError with a clear message if the path escapes.
    If must_exist=True, also raises FileNotFoundError if the path does not exist.
    """
    p = Path(raw).expanduser().resolve()
    if not any(p == root or p.is_relative_to(root) for root in _ALLOWED_ROOTS):
        raise ValueError(
            f"Path '{p}' is outside the allowed roots "
            f"({', '.join(str(r) for r in _ALLOWED_ROOTS)}). "
            "Only paths under your home directory or current working directory are allowed."
        )
    if must_exist and not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return p
from mcp.server.stdio import stdio_server
from mcp import types

import os

from ios.validators.schema_validator     import validate_schema
from ios.validators.connection_validator import validate_connections
from ios.validators.constraint_validator import validate_constraints
from ios.validators.guidelines_validator import validate_guidelines
from ios.validators.storyboard_generator import generate_storyboard
from ios.validators.xcassets_manager     import (
    export_figma_node_to_xcassets,
    add_local_or_url_to_xcassets,
)
from shared.figma_client import parse_figma_url

from android.layout_generator import generate_android_layout
from android.drawable_manager  import (
    export_figma_to_drawable,
    add_image_to_drawable,
    add_svg_to_drawable_from_bytes,
)
from ios.validators.xcassets_manager import add_svg_to_xcassets
from android.validators.layout_validator    import validate_layout    as android_validate_layout
from android.validators.naming_validator    import validate_naming    as android_validate_naming
from android.validators.material_validator  import validate_material  as android_validate_material
from android.validators.guidelines_validator import validate_guidelines as android_validate_guidelines

app = Server("mobile-ui-builder")


# ─── Tool definitions ─────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="validate_ios_storyboard",
            description=(
                "Validates a .storyboard file. "
                "Checks XML schema, orphaned outlet/action connections, "
                "broken segue references, NSLayoutConstraint ambiguity or conflicts, "
                "and Apple iOS HIG / best-practice guidelines (accessibility, Dynamic Type, "
                "safe areas, semantic colors, cell reuse identifiers, image content modes)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the .storyboard file"},
                    "checks": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["schema", "connections", "constraints", "guidelines"]
                        },
                        "default": ["schema", "connections", "constraints", "guidelines"]
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="validate_ios_storyboard_content",
            description=(
                "Same as validate_ios_storyboard but accepts raw XML content instead of a file path. "
                "Supports the same four checks: schema, connections, constraints, guidelines."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "checks": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["schema", "connections", "constraints", "guidelines"]
                        },
                        "default": ["schema", "connections", "constraints", "guidelines"]
                    }
                },
                "required": ["content"]
            }
        ),
        types.Tool(
            name="generate_ios_ui_from_image",
            description=(
                "Analyzes a UI screenshot or Figma export image and prepares it for "
                "Xcode .storyboard generation. Returns the image for visual analysis "
                "alongside instructions so the AI can extract the layout, build a "
                "Layout JSON, and call generate_storyboard_from_layout automatically. "
                "Accepts a local file path to any PNG, JPEG, or WebP image."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the UI screenshot or Figma export image file"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "If provided, write the generated .storyboard XML to this path"
                    },
                    "hints": {
                        "type": "string",
                        "description": "Optional description or notes about the UI to guide interpretation (e.g. 'login screen', 'use UITableViewController')"
                    },
                    "custom_class_prefix": {
                        "type": "string",
                        "description": "Optional prefix for generated ViewController custom class names (e.g. 'MyApp' → 'MyAppLoginViewController')"
                    }
                },
                "required": ["image_path"]
            }
        ),
        types.Tool(
            name="figma_export_to_xcassets",
            description=(
                "Exports a Figma component or frame to an Xcode .xcassets imageset. "
                "Default format is PDF (single vector file) — preferred for all icons and logos. "
                "Use PNG only for raster images (exports 1x/2x/3x density variants). "
                "Requires the FIGMA_TOKEN environment variable to be set. "
                "After export, reference the asset in a storyboard with "
                "'imageName': '<asset_name>' on a UIImageView."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "figma_url": {
                        "type": "string",
                        "description": (
                            "Figma share/copy-link URL for the component or frame to export. "
                            "In Figma: right-click the layer → 'Copy link'. "
                            "The URL must contain ?node-id=… "
                            "Example: https://www.figma.com/design/AbCdEf/MyApp?node-id=12-34"
                        )
                    },
                    "file_key": {
                        "type": "string",
                        "description": "Figma file key (alternative to figma_url). Found in the URL after /file/ or /design/."
                    },
                    "node_id": {
                        "type": "string",
                        "description": "Figma node ID (alternative to figma_url). Use ':' as separator, e.g. '12:34'."
                    },
                    "xcassets_path": {
                        "type": "string",
                        "description": "Absolute path to the .xcassets folder, e.g. /Users/me/MyApp/Assets.xcassets"
                    },
                    "asset_name": {
                        "type": "string",
                        "description": "Name for the imageset (no extension), e.g. 'icon-arrow'. Used as the image name in storyboards."
                    },
                    "format": {
                        "type": "string",
                        "enum": ["png", "pdf"],
                        "default": "pdf",
                        "description": "Export format. 'pdf' (default) exports a single vector file — recommended for all icons and logos. Use 'png' only for raster images (exports 1x/2x/3x)."
                    },
                    "scales": {
                        "type": "array",
                        "items": {"type": "integer", "enum": [1, 2, 3]},
                        "default": [1, 2, 3],
                        "description": "Which density scales to export. Only used when format is 'png'. Defaults to all three (1x, 2x, 3x)."
                    },
                    "render_as_template": {
                        "type": "boolean",
                        "default": False,
                        "description": "Set to true for icons that should be tinted at runtime (template rendering intent). Use for monochrome icons."
                    }
                },
                "required": ["xcassets_path", "asset_name"]
            }
        ),
        types.Tool(
            name="add_svg_asset",
            description=(
                "Adds a single SVG to both iOS xcassets (as PDF vector) and Android drawable (as AVD XML) "
                "in one call. Accepts a local .svg file path or raw inline SVG content. "
                "Use this instead of add_image_to_xcassets + add_image_to_drawable when the same icon "
                "or logo needs to be added to both platforms."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_source": {
                        "type": "string",
                        "description": "Absolute path to a local .svg file, or raw inline SVG XML content."
                    },
                    "asset_name": {
                        "type": "string",
                        "description": "Name for the asset (no extension). Used for both the imageset name and the drawable file name."
                    },
                    "xcassets_path": {
                        "type": "string",
                        "description": "Absolute path to the iOS .xcassets folder. Omit to skip iOS output."
                    },
                    "drawable_path": {
                        "type": "string",
                        "description": "Absolute path to the Android res/ folder (parent of drawable/). Omit to skip Android output."
                    },
                    "render_as_template": {
                        "type": "boolean",
                        "default": False,
                        "description": "iOS only. Set to true for tintable icons (template rendering intent)."
                    }
                },
                "required": ["svg_source", "asset_name"]
            }
        ),
        types.Tool(
            name="add_image_to_xcassets",
            description=(
                "Adds a local file or HTTPS image to an Xcode .xcassets imageset. "
                "PDF files (detected by .pdf extension or %PDF magic bytes) are written as a "
                "single vector imageset (recommended for icons and logos). "
                "PNG/JPG files are written as a scale variant; existing scales are preserved."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_source": {
                        "type": "string",
                        "description": "Absolute local file path or HTTPS URL. PDF files are auto-detected and written as vector imagesets."
                    },
                    "xcassets_path": {
                        "type": "string",
                        "description": "Absolute path to the .xcassets folder."
                    },
                    "asset_name": {
                        "type": "string",
                        "description": "Name for the imageset (no extension), e.g. 'icon-arrow'."
                    },
                    "scale": {
                        "type": "integer",
                        "enum": [1, 2, 3],
                        "default": 2,
                        "description": "Density scale of the provided image (1=@1x, 2=@2x, 3=@3x). Defaults to 2."
                    },
                    "render_as_template": {
                        "type": "boolean",
                        "default": False,
                        "description": "Set to true for tintable icons (template rendering intent)."
                    }
                },
                "required": ["image_source", "xcassets_path", "asset_name"]
            }
        ),
        types.Tool(
            name="generate_ios_ui_from_layout",
            description=(
                "Generates a valid Xcode .storyboard XML from a Layout JSON description. "
                "The Layout JSON describes the ViewController hierarchy, views, constraints, "
                "outlets, and segues (see layout_schema.md for the full format). "
                "Optionally validates the generated XML automatically."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "layout": {
                        "oneOf": [
                            {"type": "object",  "description": "Layout JSON object"},
                            {"type": "string",  "description": "Layout JSON as string"}
                        ],
                        "description": "Layout description following the layout_schema.md format"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "If provided, write the generated XML to this path (e.g. Main.storyboard)"
                    },
                    "validate": {
                        "type": "boolean",
                        "default": True,
                        "description": "Run the validator on the generated XML before returning"
                    }
                },
                "required": ["layout"]
            }
        ),
        types.Tool(
            name="generate_android_ui_from_image",
            description=(
                "Analyzes a UI screenshot or Figma export image and prepares it for "
                "Android layout XML generation. Returns the image for visual analysis "
                "alongside instructions so Claude can infer the Android JSON and call "
                "generate_android_ui_from_json."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "output_path": {"type": "string"},
                    "hints": {"type": "string"},
                },
                "required": ["image_path"],
            }
        ),
        types.Tool(
            name="generate_android_ui_from_json",
            description=(
                "Generates Android res/layout XML and res/values/dimens.xml from an Android JSON layout description. "
                "String resources are NOT written to res/values/strings.xml — instead, the result includes "
                "'appstrings_entries' (a dict of key→value) that must be added to the project's "
                "AppStrings.resx shared localization file (and any language variants such as .es.resx / .fr.resx). "
                "Optionally validates the generated XML."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "layout": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "string"},
                        ]
                    },
                    "output_path": {"type": "string"},
                    "validate": {"type": "boolean", "default": True},
                },
                "required": ["layout"],
            }
        ),
        types.Tool(
            name="validate_android_layout",
            description=(
                "Validates an Android layout XML file or raw XML string. "
                "Runs four checks: layout (schema + constraints), naming (IDs + filename), "
                "material (Material 3 components), guidelines (accessibility, strings, colors, dimensions)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "checks": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["layout", "naming", "material", "guidelines"],
                        },
                        "default": ["layout", "naming", "material", "guidelines"],
                    },
                    "filename": {"type": "string", "description": "Filename hint for naming validator (e.g. 'activity_login.xml')"},
                },
            }
        ),
        types.Tool(
            name="figma_export_to_drawable",
            description=(
                "Exports a Figma component to Android drawable resources. "
                "SVG format (preferred for icons/logos) exports directly from Figma as SVG, "
                "converts to a single Android Vector Drawable XML in res/drawable/. "
                "PNG format exports 1x/2x/3x/4x density variants (mdpi/xhdpi/xxhdpi/xxxhdpi) plus hdpi copy. "
                "Requires FIGMA_TOKEN environment variable."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "figma_url": {"type": "string"},
                    "file_key":  {"type": "string"},
                    "node_id":   {"type": "string"},
                    "drawable_path": {"type": "string"},
                    "asset_name":    {"type": "string"},
                    "format": {"type": "string", "enum": ["png", "svg"], "default": "png"},
                },
                "required": ["drawable_path", "asset_name"],
            }
        ),
        types.Tool(
            name="add_image_to_drawable",
            description=(
                "Adds a local image or HTTPS image to Android drawable resources. "
                "SVG files (detected by .svg extension or content) are automatically converted "
                "to Android Vector Drawable XML and written to res/drawable/ (resolution-independent). "
                "PNG/JPG files are written to res/drawable-{density}/ as raster assets. "
                "Prefer SVG input for icons and logos to produce scalable vectors."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_source":  {"type": "string"},
                    "drawable_path": {"type": "string"},
                    "asset_name":    {"type": "string"},
                    "density": {"type": "string", "default": "xxhdpi"},
                },
                "required": ["image_source", "drawable_path", "asset_name"],
            }
        ),
    ]


# ─── Tool handlers ────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # ── validate from file ────────────────────────────────────────────────────
    if name == "validate_ios_storyboard":
        try:
            p = _safe_path(arguments["path"], must_exist=True)
        except (ValueError, FileNotFoundError) as e:
            return _text({"error": str(e)})
        xml = p.read_text(encoding="utf-8")
        checks = set(arguments.get("checks", ["schema", "connections", "constraints", "guidelines"]))
        return _text(run_all_checks(xml, str(p), checks))

    # ── validate from content ─────────────────────────────────────────────────
    elif name == "validate_ios_storyboard_content":
        checks = set(arguments.get("checks", ["schema", "connections", "constraints", "guidelines"]))
        return _text(run_all_checks(arguments["content"], "<inline>", checks))

    # ── analyze image and prepare for generation ──────────────────────────────
    elif name == "generate_ios_ui_from_image":
        try:
            img_path = _safe_path(arguments["image_path"], must_exist=True)
        except (ValueError, FileNotFoundError) as e:
            return _text({"error": str(e)})

        mime, _ = mimetypes.guess_type(str(img_path))
        if not mime or not mime.startswith("image/"):
            mime = "image/png"

        img_data = base64.standard_b64encode(img_path.read_bytes()).decode("utf-8")

        hints         = arguments.get("hints", "")
        prefix        = arguments.get("custom_class_prefix", "")
        output_path   = arguments.get("output_path", "")

        instruction_lines = [
            "Analyze the UI screenshot above and generate a valid Xcode storyboard.",
            "",
            "Follow these steps:",
            "1. Identify every visible UI component (UILabel, UIButton, UITextField,",
            "   UIImageView, UIStackView, UITableView, UIScrollView, etc.).",
            "2. Determine the view hierarchy — which views are subviews of which.",
            "3. Infer Auto Layout constraints from the visual alignment and spacing.",
            "4. Build a Layout JSON object matching the layout_schema.md format used",
            "   by generate_storyboard_from_layout.",
            "   IMPORTANT: Do NOT include 'actions' in the layout JSON. Touch events",
            "   are wired in code, not in the storyboard. Only include 'outlets'.",
            "5. Call generate_storyboard_from_layout with that Layout JSON.",
            "6. When generating the companion C# ViewController class:",
            "   - First check what base class other ViewControllers in the project use",
            "     (e.g. read a few existing .cs files next to the target file).",
            "   - In an MVVM project, match the project's own base class conventions.",
            "   - If no project-specific base class is found, fall back to defaults:",
            "     UIViewController subclasses → SubscribeBaseVC",
            "     UITableViewController subclasses → SubscribeBaseTVC",
            "   - Do NOT add IBAction methods; wire touch events in code instead.",
        ]

        if hints:
            instruction_lines += ["", f"Additional context from the user: {hints}"]
        if prefix:
            instruction_lines += [f"Use '{prefix}' as the prefix for all custom ViewController class names."]
        if output_path:
            instruction_lines += [f"Pass output_path='{output_path}' to generate_storyboard_from_layout."]

        instructions = "\n".join(instruction_lines)

        return [
            types.ImageContent(type="image", data=img_data, mimeType=mime),
            types.TextContent(type="text", text=instructions),
        ]

    # ── figma → xcassets ──────────────────────────────────────────────────────
    elif name == "figma_export_to_xcassets":
        token = os.environ.get("FIGMA_TOKEN", "")
        if not token:
            return _text({"error": (
                "FIGMA_TOKEN environment variable is not set. "
                "Add it to the MCP server 'env' config in ~/.claude/claude.json:\n"
                '  "env": { "FIGMA_TOKEN": "your-token-here" }'
            )})

        try:
            _safe_path(arguments["xcassets_path"])
        except ValueError as e:
            return _text({"error": str(e)})

        # Resolve file_key + node_id — accept either figma_url or explicit params
        try:
            if "figma_url" in arguments:
                file_key, node_id = parse_figma_url(arguments["figma_url"])
            elif "file_key" in arguments and "node_id" in arguments:
                file_key = arguments["file_key"]
                node_id  = arguments["node_id"]
            else:
                return _text({"error": "Provide either 'figma_url' or both 'file_key' and 'node_id'."})

            result = export_figma_node_to_xcassets(
                file_key          = file_key,
                node_id           = node_id,
                xcassets_path     = arguments["xcassets_path"],
                asset_name        = arguments["asset_name"],
                format            = arguments.get("format", "pdf"),
                scales            = arguments.get("scales", [1, 2, 3]),
                render_as_template= arguments.get("render_as_template", False),
                token             = token,
            )
        except Exception as e:
            return _text({"error": str(e)})

        return _text(result)

    # ── SVG → both platforms ──────────────────────────────────────────────────
    elif name == "add_svg_asset":
        svg_source = arguments["svg_source"]
        asset_name = arguments["asset_name"]
        xcassets_path = arguments.get("xcassets_path")
        drawable_path = arguments.get("drawable_path")
        render_as_template = arguments.get("render_as_template", False)

        # Resolve SVG bytes (inline content or file path)
        if svg_source.lstrip().startswith("<"):
            svg_bytes = svg_source.encode("utf-8")
        else:
            try:
                p = _safe_path(svg_source, must_exist=True)
                svg_bytes = p.read_bytes()
            except (ValueError, FileNotFoundError) as e:
                return _text({"error": str(e)})

        results: dict = {}

        if xcassets_path:
            try:
                _safe_path(xcassets_path)
                results["ios"] = add_svg_to_xcassets(
                    svg_bytes, xcassets_path, asset_name, render_as_template
                )
            except Exception as e:
                results["ios"] = {"error": str(e)}

        if drawable_path:
            try:
                _safe_path(drawable_path)
                results["android"] = add_svg_to_drawable_from_bytes(
                    svg_bytes, drawable_path, asset_name
                )
            except Exception as e:
                results["android"] = {"error": str(e)}

        if not xcassets_path and not drawable_path:
            return _text({"error": "Provide at least one of xcassets_path or drawable_path."})

        return _text(results)

    # ── local/url image → xcassets ────────────────────────────────────────────
    elif name == "add_image_to_xcassets":
        try:
            _safe_path(arguments["xcassets_path"])
        except ValueError as e:
            return _text({"error": str(e)})

        image_source = arguments["image_source"]
        if not image_source.startswith("http://") and not image_source.startswith("https://"):
            try:
                _safe_path(image_source, must_exist=True)
            except (ValueError, FileNotFoundError) as e:
                return _text({"error": str(e)})

        try:
            result = add_local_or_url_to_xcassets(
                image_source      = arguments["image_source"],
                xcassets_path     = arguments["xcassets_path"],
                asset_name        = arguments["asset_name"],
                scale             = arguments.get("scale", 2),
                render_as_template= arguments.get("render_as_template", False),
            )
        except Exception as e:
            return _text({"error": str(e)})

        return _text(result)

    # ── generate + optional validate ─────────────────────────────────────────
    elif name == "generate_ios_ui_from_layout":
        layout = arguments["layout"]
        try:
            xml = generate_storyboard(layout)
        except Exception as e:
            return _text({"error": f"Generation failed: {e}"})

        result: dict = {"generated_xml": xml}

        # Optionally write to disk
        if out := arguments.get("output_path"):
            try:
                out_path = _safe_path(out)
            except ValueError as e:
                return _text({"error": str(e)})
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(xml, encoding="utf-8")
            result["written_to"] = str(out_path)

        # Optionally validate
        if arguments.get("validate", True):
            checks = {"schema", "connections", "constraints", "guidelines"}
            validation = run_all_checks(xml, result.get("written_to", "<generated>"), checks)
            result["validation"] = validation

        return _text(result)

    elif name == "generate_android_ui_from_image":
        try:
            img_path = _safe_path(arguments["image_path"], must_exist=True)
        except (ValueError, FileNotFoundError) as e:
            return _text({"error": str(e)})
        from shared.image_analyzer import load_image_for_claude
        img = load_image_for_claude(str(img_path))
        hints = arguments.get("hints", "")
        output_path = arguments.get("output_path", "")
        lines = [
            "Analyze the UI screenshot above and generate an Android layout.",
            "",
            "Steps:",
            "1. Identify every visible UI component (MaterialButton, TextInputLayout,",
            "   RecyclerView, Toolbar, MaterialCardView, TextView, ImageView, etc.).",
            "2. Determine the view hierarchy — which views are children of which.",
            "3. Build an Android JSON object matching the mobile-ui-builder format.",
            "   - Use 'ConstraintLayout' as root_layout unless the design clearly implies LinearLayout.",
            "   - Assign IDs following the convention: {screen_type}_{component_type}_{purpose}",
            "   - Use @string/ references for all text, @dimen/ for shared dimensions.",
            "   - Express nested views via the 'children' array.",
            "   - String keys/values go into the JSON 'strings' dict — they will be added to",
            "     the project's AppStrings.resx, NOT to res/values/strings.xml.",
            "4. Call generate_android_ui_from_json with that JSON.",
        ]
        if hints:
            lines += ["", f"Additional context: {hints}"]
        if output_path:
            lines += [f"Pass output_path='{output_path}' to generate_android_ui_from_json."]
        return [
            types.ImageContent(type="image", data=img["base64"], mimeType=img["media_type"]),
            types.TextContent(type="text", text="\n".join(lines)),
        ]

    elif name == "generate_android_ui_from_json":
        layout = arguments["layout"]
        try:
            gen = generate_android_layout(layout)
        except Exception as e:
            return _text({"error": f"Generation failed: {e}"})

        result_data: dict = {
            "layout_xml":        gen["layout_xml"],
            "appstrings_entries": gen["strings"],
            "appstrings_note":   (
                "Add these entries to the project's AppStrings.resx shared localization file "
                "(and any language variants such as .es.resx / .fr.resx). "
                "Do NOT write to res/values/Strings.xml."
            ),
            "dimens_xml":        gen["dimens_xml"],
            "warnings":          gen.get("warnings", []),
        }

        output_path_arg = arguments.get("output_path", "")
        if output_path_arg:
            try:
                out_path = _safe_path(output_path_arg)
            except ValueError as e:
                return _text({"error": str(e)})
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(gen["layout_xml"], encoding="utf-8")
            result_data["written_to"] = str(out_path)

        if arguments.get("validate", True):
            filename = Path(output_path_arg).name if output_path_arg else ""
            result_data["validation"] = _run_android_checks(
                gen["layout_xml"], filename=filename
            )

        return _text(result_data)

    elif name == "validate_android_layout":
        if "path" in arguments:
            try:
                p = _safe_path(arguments["path"], must_exist=True)
            except (ValueError, FileNotFoundError) as e:
                return _text({"error": str(e)})
            xml_content = p.read_text(encoding="utf-8")
            filename = p.name
        elif "content" in arguments:
            xml_content = arguments["content"]
            filename = arguments.get("filename", "")
        else:
            return _text({"error": "Provide either 'path' or 'content'."})
        checks = set(arguments.get("checks", ["layout", "naming", "material", "guidelines"]))
        return _text(_run_android_checks(xml_content, filename=filename, checks=checks))

    elif name == "figma_export_to_drawable":
        token = os.environ.get("FIGMA_TOKEN", "")
        if not token:
            return _text({"error": "FIGMA_TOKEN environment variable is not set."})
        try:
            result_data = export_figma_to_drawable(
                figma_url    = arguments.get("figma_url"),
                file_key     = arguments.get("file_key"),
                node_id      = arguments.get("node_id"),
                drawable_path= arguments["drawable_path"],
                asset_name   = arguments["asset_name"],
                format       = arguments.get("format", "png"),
                token        = token,
            )
        except Exception as e:
            return _text({"error": str(e)})
        return _text(result_data)

    elif name == "add_image_to_drawable":
        image_source = arguments["image_source"]
        if not image_source.startswith("http://") and not image_source.startswith("https://"):
            try:
                _safe_path(image_source, must_exist=True)
            except (ValueError, FileNotFoundError) as e:
                return _text({"error": str(e)})
        try:
            result_data = add_image_to_drawable(
                image_source  = image_source,
                drawable_path = arguments["drawable_path"],
                asset_name    = arguments["asset_name"],
                density       = arguments.get("density", "xxhdpi"),
            )
        except Exception as e:
            return _text({"error": str(e)})
        return _text(result_data)

    else:
        raise ValueError(f"Unknown tool: {name}")


# ─── Shared validator orchestrator ────────────────────────────────────────────

def run_all_checks(xml: str, source: str, checks: set) -> dict:
    report: dict = {"source": source, "summary": {}, "results": {}}
    total_errors = total_warnings = 0

    if "schema" in checks:
        r = validate_schema(xml)
        report["results"]["schema"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    if "connections" in checks:
        r = validate_connections(xml)
        report["results"]["connections"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    if "constraints" in checks:
        r = validate_constraints(xml)
        report["results"]["constraints"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    if "guidelines" in checks:
        r = validate_guidelines(xml)
        report["results"]["guidelines"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    report["summary"] = {
        "total_errors":   total_errors,
        "total_warnings": total_warnings,
        "status":         "PASS" if total_errors == 0 else "FAIL",
    }
    return report


def _run_android_checks(xml: str, filename: str = "",
                        checks: set | None = None) -> dict:
    if checks is None:
        checks = {"layout", "naming", "material", "guidelines"}
    report: dict = {"source": filename or "<inline>", "summary": {}, "results": {}}
    total_errors = total_warnings = 0

    if "layout" in checks:
        r = android_validate_layout(xml)
        report["results"]["layout"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    if "naming" in checks:
        r = android_validate_naming(xml, filename=filename)
        report["results"]["naming"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    if "material" in checks:
        r = android_validate_material(xml)
        report["results"]["material"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    if "guidelines" in checks:
        r = android_validate_guidelines(xml)
        report["results"]["guidelines"] = r
        total_errors   += r["error_count"]
        total_warnings += r["warning_count"]

    report["summary"] = {
        "total_errors":   total_errors,
        "total_warnings": total_warnings,
        "status":         "PASS" if total_errors == 0 else "FAIL",
    }
    return report


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _text(data: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, indent=2))]


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
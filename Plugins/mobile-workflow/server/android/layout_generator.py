"""
Android Layout Generator
Converts Android JSON description → res/layout XML + AppStrings.resx entries
"""
from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


ANDROID_NS = "http://schemas.android.com/apk/res/android"
APP_NS     = "http://schemas.android.com/apk/res-auto"

INTERACTIVE_TYPES = {
    "MaterialButton", "Button", "ImageButton",
    "TextInputLayout", "TextInputEditText", "EditText",
    "CheckBox", "RadioButton", "Spinner", "Switch",
    "RecyclerView", "ListView",
    "ScrollView", "HorizontalScrollView",
}

TOUCH_TARGET_TYPES = {"MaterialButton", "Button", "ImageButton", "TextInputLayout"}

TYPE_TO_TAG = {
    "ConstraintLayout": "androidx.constraintlayout.widget.ConstraintLayout",
    "LinearLayout": "LinearLayout",
    "FrameLayout":  "FrameLayout",
    "CoordinatorLayout": "androidx.coordinatorlayout.widget.CoordinatorLayout",
    "MaterialButton":   "com.google.android.material.button.MaterialButton",
    "TextInputLayout":  "com.google.android.material.textfield.TextInputLayout",
    "TextInputEditText":"com.google.android.material.textfield.TextInputEditText",
    "MaterialCardView": "com.google.android.material.card.MaterialCardView",
    "Toolbar":          "com.google.android.material.appbar.MaterialToolbar",
    "RecyclerView":     "androidx.recyclerview.widget.RecyclerView",
    "ScrollView":       "ScrollView",
    "HorizontalScrollView": "HorizontalScrollView",
}

CONSTRAINT_MAP = {
    "top_to_top":       ("app", "layout_constraintTop_toTopOf"),
    "top_to_bottom_of": ("app", "layout_constraintTop_toBottomOf"),
    "bottom_to_bottom": ("app", "layout_constraintBottom_toBottomOf"),
    "bottom_to_top_of": ("app", "layout_constraintBottom_toTopOf"),
    "start_to_start":   ("app", "layout_constraintStart_toStartOf"),
    "start_to_end_of":  ("app", "layout_constraintStart_toEndOf"),
    "end_to_end":       ("app", "layout_constraintEnd_toEndOf"),
    "end_to_start_of":  ("app", "layout_constraintEnd_toStartOf"),
}

MARGIN_MAP = {
    "margin_top":    "layout_marginTop",
    "margin_bottom": "layout_marginBottom",
    "margin_start":  "layout_marginStart",
    "margin_end":    "layout_marginEnd",
}

# Types that require external libraries (ConstraintLayout, RecyclerView, Material Components).
# Emit a warning at generation time so the caller knows a dependency is needed.
EXTERNAL_DEP_TYPES: set[str] = {
    "ConstraintLayout", "CoordinatorLayout",
    "RecyclerView",
    "MaterialButton", "TextInputLayout", "TextInputEditText",
    "MaterialCardView", "Toolbar",
}

TEXT_STYLE_MAP = {
    "headline1": "?attr/textAppearanceHeadline1",
    "headline2": "?attr/textAppearanceHeadline2",
    "headline3": "?attr/textAppearanceHeadline3",
    "headline4": "?attr/textAppearanceHeadline4",
    "headline5": "?attr/textAppearanceHeadline5",
    "headline6": "?attr/textAppearanceHeadline6",
    "subtitle1": "?attr/textAppearanceSubtitle1",
    "subtitle2": "?attr/textAppearanceSubtitle2",
    "body1":     "?attr/textAppearanceBody1",
    "body2":     "?attr/textAppearanceBody2",
    "caption":   "?attr/textAppearanceCaption",
    "button":    "?attr/textAppearanceButton",
}


def generate_android_layout(layout: dict | str) -> dict:
    """
    Convert Android JSON → layout XML, strings XML, dimens XML.

    Returns:
        {
          "layout_xml": str,
          "strings": dict[str, str],   # key→value for AppStrings.resx (NOT Strings.xml)
          "dimens_xml": str,
          "warnings": list[str],
        }
    """
    if isinstance(layout, str):
        import json
        layout = json.loads(layout)

    warnings: list[str] = []
    strings: dict[str, str] = dict(layout.get("strings", {}))
    needs_dimen = False

    # Support two input formats:
    # 1. Flat:   { "root_layout": "ConstraintLayout", "views": [...] }
    # 2. Nested: { "rootView": { "type": "...", "id": "...", "children": [...] } }
    root_view_data = layout.get("rootView")
    if root_view_data:
        root_layout_type = root_view_data.get("type", "ConstraintLayout")
        # Normalise fully-qualified names to short names for TYPE_TO_TAG lookup
        short_type = root_layout_type.split(".")[-1]
        root_layout = short_type
        root_tag = TYPE_TO_TAG.get(short_type, root_layout_type)
        child_views = root_view_data.get("children", [])
        root_attrs = root_view_data  # carry id / other attrs from rootView
    else:
        root_layout = layout.get("root_layout", "RelativeLayout")
        root_tag = TYPE_TO_TAG.get(root_layout, root_layout)
        child_views = layout.get("views", [])
        root_attrs = {}

    if root_layout in EXTERNAL_DEP_TYPES:
        warnings.append(
            f"Root layout type '{root_layout}' requires an external library. "
            "If the dependency is not available, use RelativeLayout or LinearLayout instead."
        )

    ET.register_namespace("android", ANDROID_NS)
    ET.register_namespace("app", APP_NS)

    root_el = ET.Element(root_tag)
    root_el.set(f"{{{ANDROID_NS}}}layout_width", "match_parent")
    root_el.set(f"{{{ANDROID_NS}}}layout_height", "match_parent")
    if rid := root_attrs.get("id"):
        root_el.set(f"{{{ANDROID_NS}}}id", f"@+id/{rid}")

    for view in child_views:
        el, view_warnings, used_dimen = _build_view(view, root_layout)
        warnings.extend(view_warnings)
        if used_dimen:
            needs_dimen = True
        root_el.append(el)

    layout_xml = _pretty_xml(root_el)
    dimens_xml  = _build_dimens_xml()

    return {
        "layout_xml": layout_xml,
        "strings":    strings,   # raw dict — caller adds to AppStrings.resx
        "dimens_xml": dimens_xml,
        "warnings":   warnings,
    }


def _build_view(view: dict, root_layout: str) -> tuple[ET.Element, list[str], bool]:
    warnings: list[str] = []
    needs_dimen = False

    view_type = view.get("type", "View")
    if view_type in EXTERNAL_DEP_TYPES:
        warnings.append(
            f"View type '{view_type}' (id='{view.get('id', '?')}') requires an external library "
            "(ConstraintLayout, RecyclerView, or Material Components). "
            "Ensure the dependency is in the project, or use a standard alternative: "
            "ConstraintLayout → RelativeLayout/LinearLayout, "
            "RecyclerView → ListView, "
            "MaterialButton → Button, "
            "TextInputEditText/TextInputLayout → EditText."
        )
    tag = TYPE_TO_TAG.get(view_type, view_type)
    el = ET.Element(tag)

    # layout_width / layout_height
    w = view.get("layout_width")
    h = view.get("layout_height")
    if not w:
        warnings.append(f"View '{view.get('id', '?')}' missing layout_width — defaulting to match_parent")
        w = "match_parent"
    if not h:
        warnings.append(f"View '{view.get('id', '?')}' missing layout_height — defaulting to wrap_content")
        h = "wrap_content"
    el.set(f"{{{ANDROID_NS}}}layout_width", w)
    el.set(f"{{{ANDROID_NS}}}layout_height", h)

    # id
    if vid := view.get("id"):
        el.set(f"{{{ANDROID_NS}}}id", f"@+id/{vid}")

    # Touch target for interactive types
    if view_type in TOUCH_TARGET_TYPES or view.get("on_click"):
        el.set(f"{{{ANDROID_NS}}}minHeight", "@dimen/min_touch_target")
        el.set(f"{{{ANDROID_NS}}}minWidth",  "@dimen/min_touch_target")
        needs_dimen = True

    # Landscape safety: warn if a container has a fixed height > 200dp and is not a scroll view
    if h not in ("match_parent", "wrap_content") and h.endswith("dp"):
        try:
            h_dp = float(h[:-2])
            if h_dp > 200 and view_type not in ("ScrollView", "HorizontalScrollView",
                                                  "ListView", "RecyclerView"):
                warnings.append(
                    f"View '{view.get('id', '?')}' has a fixed height of {h} which may clip "
                    "in landscape (available height can be as low as ~320dp). "
                    "Use wrap_content and wrap the container in a ScrollView instead."
                )
        except ValueError:
            pass

    # style
    if style := view.get("style"):
        el.set("style", style)

    # text
    if text := view.get("text"):
        el.set(f"{{{ANDROID_NS}}}text", text)

    # hint
    if hint := view.get("hint"):
        el.set(f"{{{ANDROID_NS}}}hint", hint)

    # inputType
    if input_type := view.get("input_type"):
        el.set(f"{{{ANDROID_NS}}}inputType", input_type)

    # textAppearance
    if ts := view.get("text_style"):
        el.set(f"{{{ANDROID_NS}}}textAppearance", TEXT_STYLE_MAP.get(ts, ts))

    # contentDescription
    if cd := view.get("content_description"):
        el.set(f"{{{ANDROID_NS}}}contentDescription", cd)

    # Constraints (ConstraintLayout only)
    if root_layout == "ConstraintLayout":
        for key, value in (view.get("constraints") or {}).items():
            ns_prefix, attr = CONSTRAINT_MAP.get(key, (None, None))
            if ns_prefix == "app" and attr:
                ref = "parent" if value == "parent" else f"@+id/{value}"
                el.set(f"{{{APP_NS}}}{attr}", ref)

    # Margins
    for json_key, xml_attr in MARGIN_MAP.items():
        if val := view.get(json_key):
            el.set(f"{{{ANDROID_NS}}}{xml_attr}", val)

    # Children (nested views, e.g. TextInputEditText inside TextInputLayout)
    for child in view.get("children", []):
        child_el, child_warnings, child_dimen = _build_view(child, "")
        warnings.extend(child_warnings)
        if child_dimen:
            needs_dimen = True
        el.append(child_el)

    return el, warnings, needs_dimen


def _pretty_xml(root: ET.Element) -> str:
    raw = ET.tostring(root, encoding="unicode", xml_declaration=False)
    dom = minidom.parseString(f'<?xml version="1.0" encoding="utf-8"?>{raw}')
    return dom.toprettyxml(indent="    ", encoding=None).replace(
        '<?xml version="1.0" ?>', '<?xml version="1.0" encoding="utf-8"?>'
    )


def _build_strings_xml(strings: dict[str, str]) -> str:
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    for k, v in strings.items():
        lines.append(f'    <string name="{k}">{v}</string>')
    lines.append("</resources>")
    return "\n".join(lines)


def _build_dimens_xml() -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        '    <dimen name="min_touch_target">48dp</dimen>\n'
        "</resources>"
    )

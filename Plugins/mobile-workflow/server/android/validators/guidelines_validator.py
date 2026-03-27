"""Android best-practice guidelines checks."""
from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from shared.common import Issue, result

ANDROID_NS = "http://schemas.android.com/apk/res/android"
HEX_COLOR_RE = re.compile(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$')

IMAGE_TAGS = {
    "ImageView", "ImageButton",
    "com.google.android.material.imageview.ShapeableImageView",
}
INTERACTIVE_TAGS = {
    "Button", "EditText", "CheckBox", "RadioButton", "Spinner",
    "com.google.android.material.button.MaterialButton",
    "com.google.android.material.textfield.TextInputLayout",
}


def validate_guidelines(xml: str) -> dict:
    issues: list[Issue] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return result([Issue("error", f"XML parse error: {e}", rule="schema")])

    _check_element(root, issues)
    return result(issues)


def _check_element(el: ET.Element, issues: list[Issue]) -> None:
    tag_short = el.tag.split(".")[-1] if "." in el.tag else el.tag
    vid = el.get(f"{{{ANDROID_NS}}}id", el.tag)
    ns = f"{{{ANDROID_NS}}}"

    # Accessibility: ImageView must have contentDescription
    if el.tag in IMAGE_TAGS or tag_short in IMAGE_TAGS:
        cd = el.get(f"{ns}contentDescription", "")
        ia = el.get(f"{ns}importantForAccessibility", "")
        if not cd and ia != "no":
            issues.append(Issue("error",
                f"<{tag_short}> id='{vid}' must have contentDescription "
                "or importantForAccessibility=\"no\"",
                element_id=vid, rule="accessibility_content_description"))

    # No hardcoded string literals in text/hint
    for attr in ["text", "hint"]:
        val = el.get(f"{ns}{attr}", "")
        if val and not val.startswith("@") and not val.startswith("?"):
            issues.append(Issue("error",
                f"Hardcoded string in android:{attr}='{val}' — use @string/",
                element_id=vid, rule="hardcoded_string"))

    # No hardcoded hex colors
    for attr in ["background", "textColor", "tint", "backgroundTint", "strokeColor"]:
        val = el.get(f"{ns}{attr}", "")
        if val and HEX_COLOR_RE.match(val):
            issues.append(Issue("error",
                f"Hardcoded color '{val}' in android:{attr} — use ?attr/ or @color/",
                element_id=vid, rule="hardcoded_color"))

    # Touch targets on interactive views (minHeight + minWidth required)
    if el.tag in INTERACTIVE_TAGS or tag_short in INTERACTIVE_TAGS:
        min_h = el.get(f"{ns}minHeight", "")
        min_w = el.get(f"{ns}minWidth",  "")
        if not min_h or not min_w:
            issues.append(Issue("error",
                f"<{tag_short}> id='{vid}' must have minHeight and minWidth "
                "(minimum 48dp touch target)",
                element_id=vid, rule="touch_target"))

    # ImageView: scaleType must be explicit — the default (matrix) is almost never correct
    if el.tag in IMAGE_TAGS or tag_short in IMAGE_TAGS:
        if not el.get(f"{{{ANDROID_NS}}}scaleType"):
            issues.append(Issue("error",
                f"<{tag_short}> id='{vid}' is missing android:scaleType. "
                "Add android:scaleType=\"fitCenter\" (icons/logos) or \"centerCrop\" "
                "(full-bleed photos). The default scaleType (matrix) clips content unexpectedly.",
                element_id=vid, rule="missing_scale_type"))

    # ScrollView single child
    if tag_short == "ScrollView":
        direct_children = list(el)
        if len(direct_children) > 1:
            issues.append(Issue("error",
                "ScrollView must have exactly one direct child",
                element_id=vid, rule="scrollview_child"))

    # Landscape safety: fixed layout_height > 200dp on a container that is not inside a ScrollView
    # is risky — the content clips rather than scrolls in landscape mode.
    h_val = el.get(f"{ns}layout_height", "")
    if h_val.endswith("dp"):
        try:
            h_dp = float(h_val[:-2])
            if h_dp > 200 and tag_short not in ("ScrollView", "HorizontalScrollView",
                                                  "NestedScrollView", "ListView",
                                                  "RecyclerView", "ViewPager"):
                issues.append(Issue("warning",
                    f"<{tag_short}> id='{vid}' has a fixed layout_height of {h_val}. "
                    "In landscape mode the available height can be as low as ~320dp. "
                    "Consider using wrap_content and wrapping the container in a ScrollView "
                    "so content is reachable on small screens.",
                    element_id=vid, rule="landscape_safety"))
        except ValueError:
            pass

    for child in el:
        _check_element(child, issues)
